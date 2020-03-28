#!/usr/local/bin/python3.7
import re
import json
import requests
import requests.adapters
import brotli
import pathlib


def get_text(url: str) -> (str, None):
    s = requests.Session()
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
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


def save_img(img_url: str, referer: str, save_path) -> None:
    s = requests.Session()
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    # set header as below
    headers = {
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
        'Sec-Fetch-Dest': 'image'
    }
    r = s.get(img_url, headers=headers, timeout=5, stream=True)
    with open(save_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=2048):
            f.write(chunk)


def get_comic(url: str) -> None:
    if re.match(r'(https://)?m\.dmzj\.com/view/[0-9]+/[0-9]+\.html', url) is None:
        print('[error] invalid url')
        print('possible url:')
        print('https://m.dmzj.com/view/{comic number}/{chapter number}.html')
        exit(-1)

    dom = get_text(url)

    m = re.search(r'mReader\.initData\((.*)\);', dom)
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
    content_dir = pathlib.Path('content')
    content_dir.mkdir()
    info_file = open('info.txt', 'w')

    # write info file
    info_file.write('url={}\n'.format(url))
    info_file.write('comic_name={}\n'.format(comic_name))
    info_file.write('comic_id={}\n'.format(comic_id))
    info_file.write('chapter_name={}\n'.format(chapter_title))
    info_file.write('chapter_id={}\n'.format(chapter_id))
    info_file.write('comment_count={}\n'.format(comment_count))

    # get cover
    cover_save_path = 'cover.' + comic_cover.rsplit('.', maxsplit=1)[1]
    save_img(comic_cover, referer, cover_save_path)

    # save content
    for img_url in page_url_arr:
        img_path = 'content/' + img_url.rsplit('/', maxsplit=1)[1]
        save_img(img_url, referer, img_path)


def main():
    import argparse
    import os
    # parse arg
    parser = argparse.ArgumentParser(description='download manga from https://m.dmzj.com/')
    parser.add_argument('-u', '--url', help='download from url')
    parser.add_argument('-d', '--dir', help='save to directory')
    args = parser.parse_args()

    if args.dir is not None:
        os.chdir(args.dir)
    if args.url is None:
        parser.print_help()
    else:
        get_comic(args.url)


__all__ = [get_comic]
if __name__ == '__main__':
    main()
