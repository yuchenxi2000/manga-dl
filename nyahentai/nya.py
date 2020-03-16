#!/usr/local/bin/python3.7
# -*- coding:utf-8 -*-

# 爬取 https://zh.nyahentai.cc/ 下的本子
# 命令行参数 -u, -d
# 你的 url 必须是这种形式：
# https://zh.nyahentai.cc/g/286285/list2/
# 其中 '286285' 可为其他数字

# example:
# python3.7 nya.py -u https://zh.nyahentai.cc/g/286285/list2/ -d .

import bs4
import requests
import requests.adapters
import brotli
import pathlib
import argparse

# 上面这些 pip 包请自行安装


def get_from_url(url, stream=None):
    s = requests.Session()
    # s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    # cookies = {
    #     '__cfduid': 'd15e83d73ddb21566308e9658995fa4b01584067981',
    #     'splash_i': 'false',
    #     'splashWeb-3387561-42': '1',
    # }
    cookies = None
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        # 'sec-fetch-dest': 'document',
        # 'sec-fetch-mode': 'navigate',
        # 'sec-fetch-site': 'none',
        # 'sec-fetch-user': '?1',
        # 'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    } if stream is None else{
        'accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    try:
        return s.get(url, stream=stream, timeout=5, headers=headers, cookies=cookies)
    except requests.exceptions.RequestException as e:
        print(e)
        return None


def decode_content(response):
    if response.status_code != 200:
        return None
    if 'Content-Encoding' in response.headers and response.headers['Content-Encoding'] == 'br':
        data = brotli.decompress(response.content)
        data1 = data.decode('utf-8')
        return data1
    # webpage.encoding = 'utf-8'
    if response.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(response.text)
        if encodings:
            response.encoding = encodings[0]
        else:
            response.encoding = response.apparent_encoding
    return response.text


def get_text(url):
    res = get_from_url(url)
    if res is None:
        return None
    return decode_content(res)


def write_img(url, path):
    r = get_from_url(url, True)
    if r.status_code != 200:
        return False
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=2048):
            f.write(chunk)
    return True


def try_save(img_url, save_dir):
    li = img_url.rsplit('/', maxsplit=1)
    if len(li) == 2:
        img_path = save_dir.joinpath(li[1])
        if img_path.exists():
            print('img {} exists, skip'.format(img_path))
            return True
        else:
            return write_img(img_url, img_path)
    return False


parser = argparse.ArgumentParser(description='downloads manga from https://zh.nyahentai.cc/')
parser.add_argument('-u', '--url', help='download from url')
parser.add_argument('-d', '--dir', help='save directory')
arg = parser.parse_args()

if arg.url is None or arg.dir is None:
    parser.print_help()
    exit(0)

url = arg.url
save_dir = pathlib.Path(arg.dir)
if not save_dir.exists():
    print('save directory not exist!')
    exit(-1)

page = bs4.BeautifulSoup(get_text(url), features='lxml')
imgs = page.find_all('img', class_='list-img lazyload')
title = page.find('title').text.split(' »')[0].split('»')[0]

save_dir = save_dir.joinpath(title)
if save_dir.exists():
    print('directory {} already exists. continue?'.format(save_dir))
    ans = input('Y/n: ')
    if ans != 'Y' and 'y':
        print('exit.')
        exit(0)
else:
    save_dir.mkdir()

for img in imgs:
    img_url = img['data-src']
    if not try_save(img_url, save_dir):
        img_url = img_url.rsplit('.', maxsplit=1)[0] + '.png'
        if not try_save(img_url, save_dir):
            print('failed to save {}'.format(img_url))
