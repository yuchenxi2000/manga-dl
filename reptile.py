import argparse
import pathlib
import threading
import requests
import bs4

search_url_prefix = 'https://so.azs2019.com/serch.php?keyword='


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


# dirname : pathlib.Path
def save_img(dirname, url, img_id, tid):
    r = requests.get(url, stream=True)
    junk, suffix = url.rsplit('.', maxsplit=1)
    img_name = pathlib.Path(str(img_id) + '.' + suffix)
    img_path = dirname.joinpath(img_name)
    with open(img_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=256):
            f.write(chunk)
    print('thread {} : saved {}'.format(tid, img_path))


def task(t, tid):
    save_img(t[0], t[1], t[2], tid)


pool = ThreadDL(task)


def get_all_image(save_dir, sub_dir, url):
    global pool

    url_prefix, junk = url.rsplit('/', maxsplit=1)
    url_prefix += '/'

    fullname = save_dir.joinpath(sub_dir)
    if fullname.exists():
        print('error! {} already exists'.format(fullname))
        return
    fullname.mkdir()
    if not fullname.exists():
        print('error! failed to create dir {}'.format(fullname))
        return

    img_cnt = 0
    while True:
        webpage = requests.get(url)
        # webpage.encoding = 'gb2312'
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(webpage.text)
            if encodings:
                webpage.encoding = encodings[0]
            else:
                webpage.encoding = webpage.apparent_encoding
        html = bs4.BeautifulSoup(webpage.text, features='lxml')
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


def search(keyword, file=None):
    global search_url_prefix
    if file is None:
        url = search_url_prefix + requests.utils.quote(keyword, encoding='gbk')
        webpage = requests.get(url)
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

    url_list = []
    content3 = dom.find_all('p', class_='focus')
    for c in content3:
        url_list.append(c.a['href'])

    title_list = []
    content4 = dom.find_all('a', target='_blank', title=not None)
    for c in content4:
        title_list.append(c['title'])

    title_url_map = zip(title_list, url_list)
    return title_url_map


def main():
    global search_url_prefix
    parser = argparse.ArgumentParser(description='grab racy images from zhaifuli')
    parser.add_argument('-u', '--url', help='save image from url')  # action='store_true'
    parser.add_argument('-S', '--search', help='search mode, the search keyword. \
    if \'--save\' is not specified, list results and exit. ')
    parser.add_argument('--search_url_prefix', help='change the prefix of search url')
    parser.add_argument('-s', '--save', help='directory to save images')

    args = parser.parse_args()

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
            print('please specify the directory to save images using \'--save\' argument')
            exit(-1)
    elif args.search:
        url_map = search(args.search)

        if args.save:
            save_dir = pathlib.Path(args.save)
            pool.start_task()
            for t in url_map:
                sub_dir = pathlib.Path(t[0])
                url = t[1]
                get_all_image(save_dir, sub_dir, url)
            pool.finish_task()
        else:
            for t in url_map:
                print(t)


if __name__ == '__main__':
    main()

