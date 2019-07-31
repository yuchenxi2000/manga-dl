# zfl-reptile

一个爬取racy pics的爬虫 (/ω＼) 

## 美的事物谁不喜欢呢。

关于网站是啥。我只能提供拼音（zhaifuli）。有心的人自然会找到。

自己看看就好了。

第一次写爬虫，竟爬这个，也是醉了。

## usage?

* 先装 beautifulsoup4, requests

``` shell
$ pip3 install beautifulsoup4
```

``` shell
$ pip3 install requests
```

* 命令行选项

1. -h, —help : 打印帮助然后退出
2. -s, —save : 指定保存的文件夹
3. -u, —url : 从URL下载全部图片
4. -S, —search : 根据关键词搜索图集
5. -l, -list : 从列表文件中读取每一行URL并下载
6. —search_url_prefix : 搜索功能的URL前缀（前缀+关键词 拼成URL，在网站换域名可以用此指定前缀。也可改源码，一般情况无需使用）

* 示例

1. 从 \$URL 下载，保存到 \$SAVEDIR 文件夹

``` shell
$ python3 reptile.py -u $URL -s $SAVEDIR
```

2. 搜索关键词，列出搜索结果

``` shell
$ python3 reptile.py -S $KEYWORD
```

3. 搜索关键词，下载全部

``` shell
$ python3 reptile.py -S $KEYWORD -s $SAVEDIR
```

4. 从列表下载全部

``` shell
$ python3 reptile.py -l $LIST -s $SAVEDIR
```

* 实现

主线程爬取网页，多线程下载图片。

线程池线程数可调（改源码）。

如果被反爬虫可以改成 1。

## 鱼/渔

有个教程我觉得写得很好，很喜欢作者，支持一下。

[莫烦python](https://morvanzhou.github.io/tutorials/data-manipulation/scraping/)

## Author

不留名 (>_<)
