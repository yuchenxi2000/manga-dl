import requests
import requests.adapters
import brotli
import re
import pathlib
# http://zh.a-upp.com/s/302241/ info
# http://zh.a-upp.com/g/302241/ reader


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


def save_img(s: requests.Session, img_url: str, img_path) -> None:
    headers = {
        'accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }
    r = s.get(img_url, headers=headers, stream=True, timeout=5)
    if r.status_code != 200:
        print('failed to save {}'.format(img_url))
        return
    with open(img_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=2048):
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
    url = args.url

    if args.dir is not None:
        save_dir = pathlib.Path(args.dir)
    else:
        save_dir = pathlib.Path('.')

    if re.match(r'http://zh\.a-upp\.com/g/[0-9]+/?', url) is None:
        print('invalid url. possible url:')
        print('http://zh.a-upp.com/g/302252/')
        exit(-1)

    session = requests.Session()
    session.mount('http://', requests.adapters.HTTPAdapter(max_retries=3))
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;\
q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh,en;q=0.9,ja;q=0.8,zh-CN;q=0.7',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) \
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }

    res = session.get(url, headers=headers, timeout=5)

    if res.status_code != 200:
        print(res.status_code)
        exit(-1)

    text = decode_content(res)

    # title
    # <title>[36 (Hakua)] Houkago Temptation. (New Danganronpa V3) [Digital]</title>
    title = re.search(r'<title>([^<]*)', text).group(1)
    save_dir = save_dir.joinpath(title)
    try:
        save_dir.mkdir()
    except:
        pass

    # img-url
    # <div class="img-url">//ja.comicstatic.icu/img/ja/1604763/1.jpg</div>
    # https://c.mipcdn.com/i/s/https://a.comicstatic.icu/img/ja/1604763/1.jpg
    m = re.findall(r'<div[^>]*class=["\']img-url["\'][^>]*>[^<]*comicstatic\.icu([^<]*)', text)
    for u in m:
        img_url = 'https://c.mipcdn.com/i/s/https://a.comicstatic.icu' + u
        img_name = u.rsplit('/', maxsplit=1).pop()
        img_path = save_dir.joinpath(img_name)
        if img_path.exists():
            continue
        save_img(session, img_url, img_path)


if __name__ == '__main__':
    main()
