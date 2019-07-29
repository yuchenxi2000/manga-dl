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
    path = pathlib.Path('/Users/ycx/Desktop/')
    e = path.exists()
    print(e)
    print('files : ')
    for f in path.iterdir():
        print(f)
    pass


def url_test(keyword):
    url = 'https://so.azs2019.com/serch.php?keyword='
    url += requests.utils.quote(keyword, encoding='gbk')
    webpage = requests.get(url)
    if webpage.encoding == 'ISO-8859-1':
        encodings = requests.utils.get_encodings_from_content(webpage.text)
        if encodings:
            webpage.encoding = encodings[0]
        else:
            webpage.encoding = webpage.apparent_encoding

    # dom = bs4.BeautifulSoup(webpage.text, features='lxml')
    fp = open('page.html')
    dom = bs4.BeautifulSoup(fp, features='lxml')
    content3 = dom.find_all('p', class_='focus')
    for c in content3:
        print(c.a['href'])

    fp = open('page.html', 'w')
    fp.write(webpage.text)
    fp.close()


if __name__ == '__main__':
    url_test('尤奈')
