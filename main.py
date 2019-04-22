import bs4
import requests
import os
import sys


def save_img(fullname, url, img_id):
    r = requests.get(url, stream=True)
    junk, suffix = url.rsplit('.', maxsplit=1)
    img_path = fullname + str(img_id) + '.' + suffix
    with open(img_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=128):
            f.write(chunk)
    print('saved ' + img_path)


def get_all_image(save_path, dirname, url):
    url_prefix, junk = url.rsplit('/', maxsplit=1)
    url_prefix += '/'
    fullname = save_path + dirname
    success = os.system('mkdir ' + fullname)
    if success != 0:
        print('mkdir : error')
        # exit(-1)

    img_cnt = 0

    while True:
        webpage = requests.get(url)
        webpage.encoding = 'gb2312'
        '''
        if webpage.encoding == 'ISO-8859-1':
            encodings = requests.utils.get_encodings_from_content(req.text)
            if encodings:
                encoding = encodings[0]
            else:
                encoding = webpage.apparent_encoding
        '''
        # fp = open('/Users/ycx/Desktop/page0.html', 'w')
        # fp.write(webpage.text)
        # exit(0)
        html = bs4.BeautifulSoup(webpage.text, features='lxml')
        content = html.find('article', class_='article-content')
        p_img = content.children

        for p in p_img:
            if type(p) is bs4.element.Tag:
                if p.img is not None:
                    save_img(fullname, p.img['src'], img_cnt)
                    img_cnt += 1

        link = html.find('a', text='下一页')
        if link is None:
            print('{cnt} images saved from {url}'.format(cnt=img_cnt, url=url))
            return
        url = url_prefix + link['href']


# parameter passed
argv = sys.argv
if len(argv) != 3:
    print('num of arguments must be 3. use \'-h\' for usage')
    exit(-1)
save_path = argv[1]
if save_path == '-h':
    print('usage: \nfirst argument: save folder\n \
    second argument: file containing url of images.\n \
    if you want to know how to write url file, please refer to README.md.')
    exit(0)
if save_path[-1] != '/':
    save_path += '/'

url_file = open(argv[2], 'r')
folder_name = ''
set_url = ''
line_cnt = 0
for line in url_file:
    if line_cnt % 2 == 0:
        folder_name = line
    else:
        set_url = line
        if folder_name[-1] == '\n':
            folder_name = folder_name[:-1]
        if folder_name[-1] != '/':
            folder_name += '/'
        if set_url[-1] == '\n':
            set_url = set_url[:-1]
        get_all_image(save_path, folder_name, set_url)
    line_cnt += 1
