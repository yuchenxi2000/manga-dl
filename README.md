# zfl-reptile

一个爬取racy pics的爬虫 (/ω＼)（网站：宅福利

## !notice!

请适度使用，俗话说得好，

> 小撸怡情，大撸伤身，强撸灰飞烟灭。

自己看看就好了。

第一次写爬虫，竟爬这个，也是醉了。

> 技术无分好坏。关键看怎么使用它。

## usage?

* 先装 beautifulsoup4, requests

``` shell
$ pip3 install beautifulsoup4
```

``` shell
$ pip3 install requests
```

* 命令行选项

1. -h, --help : 打印帮助然后退出
2. -s, --save : 指定保存的文件夹
3. -u, --url : 从URL下载全部图片
4. -S, --search : 根据关键词搜索图集
5. -l, --list : 从列表文件中读取每一行URL并下载
6. --search_url_prefix : 搜索功能的URL前缀（前缀+关键词 拼成URL，在网站换域名可以用此指定前缀。也可改源码，一般情况无需使用）
7. -N, --new_domain : 自动搜索新域名并更换（访问慢可试试）
8. -n, --newest : 列出最新的资源
9. -p, --page : 指定页码
10. -gl, --genlist : 把网址保存到文件
11. -v, --preview : 生成预览网页（双击 preview.html，即可在浏览器中打开。preview.html 除去了广告等内容）

* 示例

1. 从 \$URL 下载，保存到 \$SAVEDIR 文件夹

``` shell
$ python3 reptile.py -u $URL -s $SAVEDIR
```

2. 搜索 \$KEYWORD 关键词，列出第一页搜索结果

``` shell
$ python3 reptile.py -S $KEYWORD
```

3. 搜索 \$KEYWORD 关键词，列出 \$PAGE 页的搜索结果

``` shell
$ python3 reptile.py -S $KEYWORD -p $PAGE
```

4. 搜索 \$KEYWORD 关键词，下载第一页全部

``` shell
$ python3 reptile.py -S $KEYWORD -s $SAVEDIR
```

5. 搜索 \$KEYWORD 关键词，下载 \$PAGE 页全部，保存到 \$SAVEDIR

``` shell
$ python3 reptile.py -S $KEYWORD -s $SAVEDIR -p $PAGE
```

6. 从列表下载全部

``` shell
$ python3 reptile.py -l $LIST -s $SAVEDIR
```

列表格式：一行一个URL

7. 搜索关键词/查看最新内容并将网址保存到文件 \$FILE

``` shell
$ python3 reptile.py -S $KEYWORD -gl > $FILE
```

``` shell
$ python3 reptile.py -n -gl > $FILE
```

或者，将列表打印到终端：

``` shell
$ python3 reptile.py -n -gl
```

8. 生成预览 html

``` shell
$ python3 reptile.py -v $URL
```

## 实现

主线程爬取网页，多线程下载图片。

## 鱼/渔

有个教程我觉得写得很好，很喜欢作者，支持一下。

[莫烦python](https://morvanzhou.github.io/tutorials/data-manipulation/scraping/)