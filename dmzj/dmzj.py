#!/usr/local/bin/python3.7
import re
import json
import requests
import requests.adapters
import brotli
import pathlib

valid_chapter_view_url = r'^https://m\.dmzj\.com/view/[0-9]+/[0-9]+\.html$'
valid_comic_info_url = r'^https://m\.dmzj\.com/info/(.*)\.html$'


def try_mkdir(dir: pathlib.Path) -> None:
    if dir.is_dir():
        ans = input('directory {} already exists. continue? Y/n: '.format(dir))
        while True:
            if ans == 'Y' or 'y':
                return
            elif ans == 'N' or 'n':
                print('exit.')
                exit(0)
            else:
                ans = input('Y/n: ')
    elif not dir.exists():
        try:
            dir.mkdir()
        except:
            print('cannot mkdir {}'.format(dir))
            exit(-1)
    else:
        print('{} exists, but not a directory'.format(dir))
        exit(-1)


def try_open_skip(file: pathlib.Path, mode: str):
    if file.is_file():
        print('{} exists, skip'.format(file))
        return None
    elif not file.exists():
        return open(file, mode)
    else:
        print('{} exists, but not a file'.format(file))
        exit(-1)


def get_text(s: requests.Session, url: str) -> (str, None):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    response = s.get(url, timeout=5, headers=headers)
    if response.status_code != 200:
        return None
    if 'Content-Encoding' in response.headers and response.headers['Content-Encoding'] == 'br':
        data = brotli.decompress(response.content)
        data1 = data.decode('utf-8')
        return data1
    if response.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(response.text)
        if encodings:
            response.encoding = encodings[0]
        else:
            response.encoding = response.apparent_encoding
    return response.text


def save_img(s: requests.Session, img_url: str, referer: str, save_path) -> None:
    # set header as below
    headers = {
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
        'Sec-Fetch-Dest': 'image'
    }
    r = s.get(img_url, headers=headers, timeout=5, stream=True)

    f = try_open_skip(save_path, 'wb')
    if f is None:
        return
    for chunk in r.iter_content(chunk_size=2048):
        f.write(chunk)
    f.close()


def get_chapter(s: requests.Session, url: str, dir: pathlib.Path) -> None:
    """
    possible url:
    https://m.dmzj.com/view/{comic number}/{chapter number}.html
    """
    print('download chapter from {}'.format(url))
    dom = get_text(s, url)

    m = re.search(r'mReader\.initData\((.*)\)', dom)
    args = m.group(1).rsplit(',', maxsplit=2)

    # 3 arguments of js func window.mReader.initData
    init_chap = json.loads(args[0])
    comic_name = args[1].split('"')[1]
    comic_cover = 'https://images.dmzj.com/' + args[2].split('"')[1]

    # dump json init_chap
    comment_count = init_chap['comment_count']
    chapter_id = init_chap['id']
    comic_id = init_chap['comic_id']
    chapter_title = init_chap['chapter_name']
    page_url_arr = init_chap['page_url']

    # set referer
    referer = 'https://m.dmzj.com/view/{}/{}.html'.format(comic_id, chapter_id)

    # mkdir
    content_dir = dir.joinpath('content')
    try_mkdir(content_dir)

    # write info file
    info_file = try_open_skip(dir.joinpath('info.txt'), 'w')
    if info_file is not None:
        info_file.write('url={}\n'.format(url))
        info_file.write('comic_name={}\n'.format(comic_name))
        info_file.write('comic_id={}\n'.format(comic_id))
        info_file.write('chapter_name={}\n'.format(chapter_title))
        info_file.write('chapter_id={}\n'.format(chapter_id))
        info_file.write('comment_count={}\n'.format(comment_count))

    # get cover
    cover_save_path = dir.joinpath('cover.' + comic_cover.rsplit('.', maxsplit=1)[1])
    save_img(s, comic_cover, referer, cover_save_path)

    # save content
    for img_url in page_url_arr:
        img_path = content_dir.joinpath(img_url.rsplit('/', maxsplit=1)[1])
        save_img(s, img_url, referer, img_path)


def get_comic(s: requests.Session, url: str, dir: pathlib.Path) -> None:
    """
    possible url:
    https://m.dmzj.com/info/{manga name}.html
    """
    print('download comic from {}'.format(url))

    text = get_text(s, url)
    m = re.search(r'initIntroData\((.*)\)', text)
    chapters = json.loads(m.group(1))

    for c in chapters[0]['data']:
        title = c['chapter_name']
        chapter_url = 'https://m.dmzj.com/view/{0}/{1}.html'.format(c['comic_id'], c['id'])
        chapter_dir = dir.joinpath(title)
        try_mkdir(chapter_dir)
        get_chapter(s, chapter_url, chapter_dir)


def main():
    import argparse
    # parse arg
    parser = argparse.ArgumentParser(description='download manga from https://m.dmzj.com/')
    parser.add_argument('-u', '--url', help='download from url')
    parser.add_argument('-d', '--dir', help='save to directory')
    args = parser.parse_args()

    if args.dir is None:
        dir = pathlib.Path('.')
    else:
        dir = pathlib.Path(args.dir)
        if not dir.exists():
            print('directory {} not exists'.format(args.dir))
            exit(-1)

    if args.url is None:
        parser.print_help()
    else:
        s = requests.Session()
        s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
        if re.match(valid_chapter_view_url, args.url) is not None:
            get_chapter(s, args.url, dir)
        elif re.match(valid_comic_info_url, args.url) is not None:
            get_comic(s, args.url, dir)
        else:
            print('invalid url, possible url:')
            print('https://m.dmzj.com/view/{comic number}/{chapter number}.html')
            print('https://m.dmzj.com/info/{manga name}.html')
            exit(-1)


__all__ = [
    'get_comic',
    'get_chapter'
]
if __name__ == '__main__':
    main()
