#!/usr/local/bin/python3.7
import re
import requests
import brotli
import pathlib
"""
image: http://image.mangabz.com/2/1525/72736/1_5136.jpg?cid=72736&key=c5bb3acd0d5272282c34f61147c44d32&uk=
index: http://www.mangabz.com/m72736
ajax: http://www.mangabz.com/m72736/chapterimage.ashx?cid=72736&page=1&key=&_cid=72736&_mid=1525&_dt=2020-04-03+19%3A46%3A33&_sign=39178ce4bd60491dd9977e9a818a56c5
image url: /2/mid/cid/image_name
"""


def decode_text(res):
    if 'Content-Encoding' in res.headers and res.headers['Content-Encoding'] == 'br':
        data = brotli.decompress(res.content)
        text = data.decode('utf-8')
    elif res.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(res.text)
        if encodings:
            res.encoding = encodings[0]
        else:
            res.encoding = res.apparent_encoding
        text = res.text
    else:
        text = res.text
    return text


def get_index(s: requests.Session, url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }
    res = s.get(url, headers=headers)
    return decode_text(res)


def get_image_url(s: requests.Session, url: str) -> (dict, str):
    text = get_index(s, url)

    # number
    MANGABZ_CID = re.search(r'var +MANGABZ_CID *= *([0-9]*)', text).group(1)
    MANGABZ_MID = re.search(r'var +MANGABZ_MID *= *([0-9]*)', text).group(1)
    MANGABZ_IMAGE_COUNT = int(re.search(r'var +MANGABZ_IMAGE_COUNT *= *([0-9]*)', text).group(1))

    # string
    MANGABZ_VIEWSIGN_DT = re.search(r'var +MANGABZ_VIEWSIGN_DT *= *[\'|"]([0-9a-z:\- ]*)[\'|"]', text).group(1)
    MANGABZ_VIEWSIGN = re.search(r'var +MANGABZ_VIEWSIGN *= *[\'|"]([0-9a-z]*)[\'|"]', text).group(1)

    # fill in img dict
    imgs = {}
    MANGABZ_PAGE = 1
    ajax_url = url + 'chapterimage.ashx' if url.endswith('/') else url + '/chapterimage.ashx'
    while MANGABZ_PAGE <= MANGABZ_IMAGE_COUNT:
        if str(MANGABZ_PAGE) in imgs:
            print('debug: skip {}'.format(MANGABZ_PAGE))
            MANGABZ_PAGE += 1
            continue
        params = {
            'cid': MANGABZ_CID,
            'page': MANGABZ_PAGE,
            'key': None,
            '_cid': MANGABZ_CID,
            '_mid': MANGABZ_MID,
            '_dt': MANGABZ_VIEWSIGN_DT,
            '_sign': MANGABZ_VIEWSIGN
        }
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
            'Referer': url,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        ajax_res = s.get(ajax_url, headers=headers, params=params)
        code = decode_text(ajax_res)
        img_info = code.rsplit(',', maxsplit=3)[1]
        m = re.findall(r'(([0-9]+)_[0-9]+)', img_info)
        for i in m:
            imgs[i[1]] = i[0]
        MANGABZ_PAGE += 1
    img_prefix = 'http://image.mangabz.com/2/{}/{}/'.format(MANGABZ_MID, MANGABZ_CID)
    return imgs, img_prefix


def save_img(s: requests.Session, img_url: str, referer: str, img_path):
    # set referer as http://www.mangabz.com/m72736/
    headers = {
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }
    res = s.get(img_url, headers=headers, stream=True)
    with open(img_path, 'wb') as f:
        for chunk in res.iter_content(chunk_size=2048):
            f.write(chunk)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='downloads manga from http://www.mangabz.com/')
    parser.add_argument('-u', '--url', help='download from url')
    parser.add_argument('-d', '--dir', help='save directory')
    args = parser.parse_args()

    if args.url is None:
        parser.print_help()
        exit(0)

    if args.dir:
        save_path = pathlib.Path(args.dir)
        if not save_path.exists():
            print('save dir not exists')
            exit(-1)
    else:
        save_path = pathlib.Path('.')

    if re.match(r'http://www\.mangabz\.com/m[0-9]+/?', args.url) is None:
        print('invalid url. possible url:')
        print('http://www.mangabz.com/m72736')
        exit(-1)

    session = requests.Session()
    imgs, img_prefix = get_image_url(session, args.url)
    for n in imgs:
        img_name = n+'.jpg'
        img_url = img_prefix+imgs[n]+'.jpg'
        img_path = save_path.joinpath(img_name)
        save_img(session, img_url, args.url, img_path)

