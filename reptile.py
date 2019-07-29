import pathlib
import threading
import requests
import bs4


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
        for chunk in r.iter_content(chunk_size=128):
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
        # fp = open('/Users/ycx/Desktop/page0.html', 'w')
        # fp.write(webpage.text)
        # exit(0)
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
            print('{cnt} images saved from {url}'.format(cnt=img_cnt, url=url))
            return
        url = url_prefix + link['href']


def main():
    save_dir = pathlib.Path('/Users/ycx/Desktop/mm/')
    sub_dir = pathlib.Path('尤奈0/')
    url = 'https://d265aj.com/xiurenwang/2019/0113/6404.html'

    pool.start_task()
    get_all_image(save_dir, sub_dir, url)
    pool.finish_task()


if __name__ == '__main__':
    main()
