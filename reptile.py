#!/usr/local/bin/python3.7
import argparse
import pathlib
import threading
import requests
import requests.adapters
import bs4

search_url_prefix = 'https://so.azs2019.com/serch.php?keyword='
domain_get_url = 'https://dzs.zhaifulifabu.com:9527/index.html'
new_domain = None


class ThreadDL:
    cond = threading.Condition()
    th = []
    li = []
    finished = False
    num_thread = 0

    def __init__(self, task, num_thread=4):  # task : function type, args : 2
        self.num_thread = num_thread
        for tid in range(num_thread):
            self.th.append(threading.Thread(target=self._task, args=[task, tid]))

    def _task(self, task, thread_id):
        while True:
            if self.cond.acquire():
                if len(self.li) == 0:
                    if not self.finished:
                        self.cond.wait()
                        self.cond.release()
                    else:
                        self.cond.release()
                        return
                else:
                    t = self.li.pop()
                    self.cond.release()
                    task(t, thread_id)

    def start_task(self):
        self.finished = False
        for t in self.th:
            t.start()

    def finish_task(self):
        if self.cond.acquire():
            self.finished = True
            self.cond.notifyAll()
            self.cond.release()

    def commit_task(self, t):
        if self.cond.acquire():
            self.li.append(t)
            self.cond.notifyAll()
            self.cond.release()


def get_new_domain():
    global domain_get_url
    content = get_from_url(domain_get_url)

    if content is None:
        return None

    # correct encoding
    if content.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(content.text)
        if encodings:
            content.encoding = encodings[0]
        else:
            content.encoding = content.apparent_encoding

    page = bs4.BeautifulSoup(content.text, features='lxml')
    links = page.find_all('a', class_='panel')
    return links[0].text


def get_domain_from_url(url):
    protocol = url.split('//', maxsplit=1)
    if len(protocol) == 1:
        remain = protocol[0]
    else:
        remain = protocol[1]
    domain = remain.split('/', maxsplit=1)
    return domain[0]


def set_domain(url, ndomain):
    protocol = url.split('//', maxsplit=1)
    if len(protocol) == 1:
        remain = protocol[0]
        protocol = None
    else:
        remain = protocol[1]
        protocol = protocol[0]
    domain = remain.split('/', maxsplit=1)
    if len(domain) == 1:
        body = None
        domain = domain[0]
    else:
        body = domain[1]
        domain = domain[0]
    result = ''
    if protocol is not None:
        result += protocol + '//'
    result += ndomain
    if body is not None:
        result += '/' + body
    return result


def get_from_url(url, stream=None):
    s = requests.Session()
    s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    headers = {
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }if stream is None else{
        'accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    try:
        return s.get(url, stream=stream, timeout=5, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return None


# dirname : pathlib.Path
def save_img(dirname, url, img_id, tid):
    junk, suffix = url.rsplit('.', maxsplit=1)
    img_name = pathlib.Path(str(img_id) + '.' + suffix)
    img_path = dirname.joinpath(img_name)

    if img_path.exists():
        return

    # r = requests.get(url, stream=True)
    r = get_from_url(url, True)
    if r is None:
        return
    with open(img_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=256):
            f.write(chunk)
    print('thread {} : saved {}'.format(tid, img_path))


def task(t, tid):
    save_img(t[0], t[1], t[2], tid)


pool = ThreadDL(task)


def get_all_image(save_dir, sub_dir, url):
    global pool
    global new_domain

    if new_domain is not None:
        url = set_domain(url, new_domain)

    # auto correct for url like this: '/2016/0328/6813.html'
    # search and add a domain automatically
    if url[0] == '/':
        if new_domain is None:
            new_domain = get_domain_from_url(get_new_domain())
        url = 'https://' + new_domain + url

    url_prefix, junk = url.rsplit('/', maxsplit=1)
    url_prefix += '/'
    url = url.split('\n')[0]

    fullname = pathlib.Path()

    img_cnt = 0
    while True:
        # webpage = requests.get(url)
        webpage = get_from_url(url)
        if webpage is None:
            return
        # webpage.encoding = 'gb2312'
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(webpage.text)
            if encodings:
                webpage.encoding = encodings[0]
            else:
                webpage.encoding = webpage.apparent_encoding
        html = bs4.BeautifulSoup(webpage.text, features='lxml')

        if img_cnt == 0:  # make dir
            if sub_dir is None:
                title = html.find('h1', class_='article-title')
                sub_dir = pathlib.Path(title.text)
            fullname = save_dir.joinpath(sub_dir)
            if fullname.exists():
                print('warning: {} already exists'.format(fullname))
                # return
            else:
                fullname.mkdir()
                if not fullname.exists():
                    print('error! failed to create dir {}'.format(fullname))
                    return

        content = html.find('article', class_='article-content')
        p_img = content.children

        for p in p_img:
            if type(p) is bs4.element.Tag:
                if p.img is not None:
                    t = (fullname, p.img['src'], img_cnt)
                    pool.commit_task(t)
                    img_cnt += 1

        link = html.find('a', text='下一页')
        if link is None:
            print('{cnt} images from {url}'.format(cnt=img_cnt, url=url))
            return
        url = url_prefix + link['href']


def preview(url, fp):
    global new_domain

    fp.write('<!DOCTYPE html>\n\
                <html>\n\
                <head>\n\
                <meta charset="utf-8">\n\
                <meta name="description" content="zhaifuli-preview">\n\
                <title>zhaifuli-preview</title>\n\
                <link rel="stylesheet" type="text/css" href="style.css">\n\
                </head>\n\
                <body>\n\
                <div id="article-title"><h1 class="article-title"><a href="')

    if new_domain is not None:
        url = set_domain(url, new_domain)

    # auto correct for url like this: '/2016/0328/6813.html'
    # search and add a domain automatically
    if url[0] == '/':
        if new_domain is None:
            new_domain = get_domain_from_url(get_new_domain())
        url = 'https://' + new_domain + url

    url_prefix, junk = url.rsplit('/', maxsplit=1)
    url_prefix += '/'
    url = url.split('\n')[0]

    fp.write(url)

    img_cnt = 0
    while True:
        # webpage = requests.get(url)
        webpage = get_from_url(url)
        if webpage is None:
            return
        # webpage.encoding = 'gb2312'
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(webpage.text)
            if encodings:
                webpage.encoding = encodings[0]
            else:
                webpage.encoding = webpage.apparent_encoding
        html = bs4.BeautifulSoup(webpage.text, features='lxml')

        if img_cnt == 0:  # get title
            title = html.find('h1', class_='article-title')
            fp.write('" rel="noopener noreferrer">\n')
            fp.write(str(title.text))
            fp.write('</a></h1></div>\n\
                    <div>\n\
                    <p id="pageinfo"></p>\n\
                    <p>goto page: <input id="change-page", type="text" name="pagenum" onchange="gotoPage(this.value)" /></p>\n\
                    <div>\n\
                    <button type="button" onclick="prev()">prev</button>\n\
                    <button type="button" onclick="next()">next</button>\n\
                    </div>\n\
                    </div>\n\
                    <div id="image-content"></div>\n\
                    <div id="image-bottom">\n\
                    <button id="gotop", type="button" onclick="goTop()">top</button>\n\
                    </div>\n\
                    <hr />\n\
                    <p id="bottom-notice">generated by reptile.py</p>\n\
                    <script>\n\
                    var images = [\n')

        content = html.find('article', class_='article-content')
        p_img = content.children

        for p in p_img:
            if type(p) is bs4.element.Tag:
                if p.img is not None:
                    fp.write('"' + str(p.img['src']) + '",\n')
                    img_cnt += 1

        link = html.find('a', text='下一页')
        if link is None:
            fp.write(']\n\
                    </script>\n\
                    <script src="util.js"></script>\n\
                    </body>\n\
                    </html>\n')
            return
        url = url_prefix + link['href']


def search(keyword, page, file=None):
    global search_url_prefix
    if file is None:
        url = search_url_prefix + requests.utils.quote(keyword, encoding='gbk')
        if page > 1:
            url += '&page='
            url += str(page)
        # webpage = requests.get(url)
        webpage = get_from_url(url)
        if webpage is None:
            return
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(webpage.text)
            if encodings:
                webpage.encoding = encodings[0]
            else:
                webpage.encoding = webpage.apparent_encoding
        dom = bs4.BeautifulSoup(webpage.text, features='lxml')
    else:
        fp = open(file)
        dom = bs4.BeautifulSoup(fp, features='lxml')

    # get current page & total page
    pagenum = dom.find('li', class_='active')
    current, total = pagenum.text.split('/', maxsplit=1)

    # get all the urls and titles
    url_list = []
    content3 = dom.find_all('p', class_='focus')
    for c in content3:
        url_list.append(c.a['href'])

    title_list = []
    content4 = dom.find_all('a', target='_blank', title=not None)
    for c in content4:
        title_list.append(c['title'])

    title_url_map = zip(title_list, url_list)
    return int(current), int(total), title_url_map


def newest(page, file=None):
    global new_domain
    if new_domain is None:
        new_domain = get_domain_from_url(get_new_domain())
        if new_domain is None:
            print('error: failed to get new domain')
            return
    if file is None:
        url = 'https://' + new_domain + '/page/' + str(page) + '.html'
        # webpage = requests.get(url)
        webpage = get_from_url(url)
        if webpage is None:
            return
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(webpage.text)
            if encodings:
                webpage.encoding = encodings[0]
            else:
                webpage.encoding = webpage.apparent_encoding
        dom = bs4.BeautifulSoup(webpage.text, features='lxml')
    else:
        fp = open(file)
        dom = bs4.BeautifulSoup(fp, features='lxml')

    # get all the urls and titles
    url_list = []
    title_list = []

    c = dom.find_all('a', target="_blank", class_=None)
    for l in c:
        if l.span is None:
            url_list.append(l['href'])
            title_list.append(l['title'])
        else:
            break

    title_url_map = zip(title_list, url_list)
    return title_url_map


def print_map(url_map):
    num = 1
    for t in url_map:
        print('{}\t{}'.format(num, t[0]))
        print('\t{}'.format(t[1]))
        num += 1


# def gen_list(url_map, path):
#     list_file = open(path, 'w')
#     for t in url_map:
#         list_file.write(t[1] + ' ' + t[0] + '\n')
#     list_file.close()


def gen_list(url_map):
    for t in url_map:
        print(t[1] + ' ' + t[0])


def main():
    global search_url_prefix
    global new_domain

    parser = argparse.ArgumentParser(description='grab racy images from zhaifuli')
    parser.add_argument('-u', '--url', help='save image from url')  # action='store_true'
    parser.add_argument('-S', '--search', help='search mode, the search keyword. \
    if \'--save\' is not specified, list results and exit. ')
    parser.add_argument('--search_url_prefix', help='change the prefix of search url')
    parser.add_argument('-s', '--save', help='directory to save images')
    parser.add_argument('-l', '--list', help='download from url in file')
    parser.add_argument('-p', '--page', help='page number')
    parser.add_argument('-N', '--new_domain', help='automatically get new domain & apply', action='store_true')
    parser.add_argument('-n', '--newest', help='get newest resources', action='store_true')
    parser.add_argument('-gl', '--genlist', help='generate list file', action='store_true')
    parser.add_argument('-v', '--view', help='generate preview html')
    parser.add_argument('-f', '--file', help='html file')

    args = parser.parse_args()

    # get new domain
    if args.new_domain:
        link = get_new_domain()
        if link is None:
            print('error: failed to get new domain')
        else:
            new_domain = get_domain_from_url(link)
            print('use new domain: {}'.format(new_domain))

    # change url prefix
    if args.search_url_prefix:
        search_url_prefix = args.search_url_prefix

    if args.url:
        if args.save:
            save_dir = pathlib.Path(args.save)
            url = args.url

            pool.start_task()
            get_all_image(save_dir, None, url)
            pool.finish_task()
        else:
            parser.error('please specify the directory to save images using \'--save\' argument')
    elif args.search:
        page = 1
        if args.page:
            page = int(args.page)
        currentpage, totalpage, url_map = search(args.search, page)
        if not args.genlist:
            print('current page: {}'.format(currentpage))
            print('total page: {}'.format(totalpage))
            print('use -p to specify the page number.')
        if args.save:
            save_dir = pathlib.Path(args.save)
            pool.start_task()
            for t in url_map:
                sub_dir = pathlib.Path(t[0])
                url = t[1]
                get_all_image(save_dir, sub_dir, url)
            pool.finish_task()
        elif args.genlist:
            gen_list(url_map)
        else:
            print_map(url_map)
    elif args.list:
        list_file = pathlib.Path(args.list)
        if not list_file.exists():
            parser.error('list file not found.')
        if not args.save:
            parser.error('please specify the directory to save images using \'--save\' argument')
        save_dir = pathlib.Path(args.save)
        with open(list_file) as fp:
            pool.start_task()
            for url in fp:
                url = url.split(' ')[0]
                get_all_image(save_dir, None, url)
            pool.finish_task()
    elif args.newest:
        page = 1
        if args.page:
            page = int(args.page)

        url_map = newest(page)
        if args.save:
            save_dir = pathlib.Path(args.save)
            pool.start_task()
            for t in url_map:
                sub_dir = pathlib.Path(t[0])
                url = t[1]
                get_all_image(save_dir, sub_dir, url)
            pool.finish_task()
        elif args.genlist:
            gen_list(url_map)
        else:
            print('current page: {}'.format(page))
            print('use -p to specify the page number.')
            print_map(url_map)
    elif args.view:
        if args.file:
            fp = open(args.file, 'w')
        else:
            fp = open('preview.html', 'w')
        if fp is None:
            parser.error('can\'t open file')
        preview(args.view, fp)
        fp.close()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

