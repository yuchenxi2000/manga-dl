#!/usr/local/bin/python3.7
# -*- coding:utf-8 -*-

# 爬取 https://erozine.jp/ 下的本子
# 命令行参数 -u, -d
# 你的 url 必须是这种形式：
# https://erozine.jp/eromanga/gf_face_white_sirako

# example:
# python3.7 erozine.py -u https://erozine.jp/eromanga/gf_face_white_sirako -d .

# 设置proxy：
# --proxy="socks5://127.0.0.1:1080"
# --proxy="http://127.0.0.1:8080"

import bs4
import requests
import requests.adapters
import brotli
import pathlib
import argparse

# 上面这些 pip 包请自行安装


def get_from_url(url, stream=None):
    s = requests.Session()

    if proxy_server is not None:
        s.proxies = {"http": proxy_server, "https": proxy_server}

    # s.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    s.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
    cookies = None
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
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


def confirm_yes(s):
    print(s)
    ans = input('Y/n: ')
    if ans != 'Y' and 'y':
        print('exit.')
        exit(0)


# parse arg
parser = argparse.ArgumentParser(description='download manga from https://erozine.jp/')
parser.add_argument('-u', '--url', help='download from url')
parser.add_argument('-d', '--dir', help='save directory')
parser.add_argument('--proxy', help='set proxy server')
arg = parser.parse_args()

# set proxy
proxy_server = arg.proxy

# url, save dir
url = arg.url
if url is None:
    print('url is none!')
    exit(-1)
save_dir = pathlib.Path(arg.dir)
if not save_dir.exists():
    print('save directory not exists!')
    exit(-1)

# get info from website
raw = get_text(url)
if raw is None:
    print('cannot get {}'.format(url))
    exit(-1)
page = bs4.BeautifulSoup(raw, features='lxml')
article = page.find('div', id='article_body')
info = article.div
title = info.h3.string
author = info.span.string

# main directory
save_dir = save_dir.joinpath('{} - {}'.format(title, author))
if save_dir.exists():
    confirm_yes('directory {} already exists. continue?'.format(save_dir))
else:
    save_dir.mkdir()

# info.txt
info_file_path = save_dir.joinpath('info.txt')
if info_file_path.exists():
    confirm_yes('info.txt already exists. continue?')
info_file = open(info_file_path, 'w')

# write info.txt
info_file.write('{}\n'.format(page.find('h1', id='article_title').string))
info_file.write('{}\n'.format(article.p.string))
info_file.write('title: {}\n'.format(title))
info_file.write('author: {}\n'.format(author))
for line in info.find_all('br'):
    info_file.write('{}\n'.format(line.next_sibling))

# img dir
img_dir = save_dir.joinpath('manga')
if img_dir.exists():
    confirm_yes('manga directory already exists. continue?')
else:
    img_dir.mkdir()

# write img
for img in article.find_all('img'):
    img_url = img['src']
    if not try_save(img_url, img_dir):
        print('failed to save {}'.format(img_url))
