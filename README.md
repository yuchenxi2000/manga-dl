# zfl-reptile

一个爬取racy pics的爬虫 (/ω＼) 

## 美的事物谁不喜欢呢。

关于网站是啥。我只能提供拼音（zhaifuli）。有心的人自然会找到。

自己看看就好了。

第一次写爬虫，竟爬这个，也是醉了。

## usage?

先装beautifulsoup4, requests

``` shell
$ pip3 install beautifulsoup4
```

``` shell
$ pip3 install requests
```

装好后在命令行运行下面指令，

$SAVE_FOLDER 是你想保存的文件夹

$URL_FILE 是存有URL的文件。格式：一行子文件夹名（在你想保存的文件夹下的子文件夹，程序每读入两行，爬一个网页，为一个网页新建一个保存图片的文件夹），一行URL。注意你只能下上面网站的图片，其他网站请自学爬虫后自己写。

``` shell
$ python3 main.py $SAVE_FOLDER $URL_FILE
```

比如：

``` shell
$ python3 main.py ./pics/ url.txt
```

现在暂时只能自行添加URL，后面可能会自动化。不过你想想，下之前难道不挑过吗（？！）。

## 鱼/渔

有个教程我觉得写得很好，很喜欢作者，支持一下。

[莫烦python](https://morvanzhou.github.io/tutorials/data-manipulation/scraping/)

## Author

不留名 (>_<)
