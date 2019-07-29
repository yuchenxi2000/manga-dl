#!/usr/bin/python3
import json
import pathlib
import requests
import bs4


def json_test():
    data = {
        'id': 1,
        'name': 'yuchenxi'
    }
    jsonStr = json.dumps(data)
    print(jsonStr)
    jsonObj = json.loads(jsonStr)
    print('id : {}'.format(jsonObj['id']))
    print('name : {}'.format(jsonObj['name']))


def path_test():
    path = pathlib.Path('test/dir1/')
    path = path.joinpath('1.txt')
    fp = open(path, 'w+')
    fp.write('123\n')
    fp.close()


def url_test(keyword, file=None):
    if file is None:
        url = 'https://so.azs2019.com/serch.php?keyword='
        url += requests.utils.quote(keyword, encoding='gbk')
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

    content3 = dom.find_all('p', class_='focus')
    for c in content3:
        print(c.a['href'])


if __name__ == '__main__':
    url_test('尤奈', file='page.html')
    # path_test()
