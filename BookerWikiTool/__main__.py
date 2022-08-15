#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-

import argparse
import requests
from readability import Document
import tempfile
import uuid
import subprocess as subp
import re
import os
import json
import yaml
from urllib.parse import quote_plus
from os import path
from pyquery import PyQuery as pq
from datetime import datetime
from collections import OrderedDict
from EpubCrawler.img import process_img
from EpubCrawler.util import safe_mkdir
from . import __version__
from .bili import *
from .util import *

def account_handle(args):
    if not args.file.endswith('.md'):
        print('请提供 markdown 文件')
        return
    print(args.file)
    cont = open(args.file, encoding='utf8').read()
    total, zh_count, en_count = account_words(cont)
    print(f'中文字数：{zh_count}\n英文字数：{en_count}\n总字数：{total}')

def fix_handle(args):
    if not args.file.endswith('.md'):
        print('请提供 markdown 文件')
        return
    cont = open(args.file, encoding='utf8').read()
    dir = path.dirname(args.file)
    rm = re.search(RE_TITLE, cont, flags=re.M)
    if not rm: 
        print(f'{args.file} 未找到标题')
        return
    title = rm.group(1)
    nfname = re.sub(r'\s', '-', fname_escape(title)) + '.md'
    nfname = path.join(dir, nfname)
    print(nfname)
    os.rename(args.file, nfname)

def download_handle(args):
    html = requests.get(
        args.url,
        headers=default_hdrs,
    ).content.decode(args.encoding, 'ignore')
    
    # 解析标题
    rt = pq(html)
    el_title = rt.find('title').eq(0)
    title = el_title.text().strip()
    el_title.remove()
    
    # 判断是否重复
    title_esc = re.sub(r'\s', '-', fname_escape(title))
    fname = f'docs/{title_esc}.md'
    if path.isfile(fname):
        print(f'{title} 已存在')
        return
    
    # 解析内容并下载图片
    co = Document(str(rt)).summary()
    co = pq(co).find('body').html()
    imgs = {}
    co = process_img(co, imgs, img_prefix='img/', page_url=args.url)
    html = f'''
    <html><body>
    <h1>{title}</h1>
    <blockquote>
    来源：<a href='{args.url}'>{args.url}</a>
    </blockquote>
    {co}</body></html>
    '''
    
    # 转换 md
    md = tomd(html)
    # md = re.sub(RE_CODE_BLOCK, code_replace_func, md)
    yaml_head = '\n'.join([
        '<!--yml',
        'category: ' + args.category,
        'date: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '-->',
    ])
    md = f'{yaml_head}\n\n{md}'
    
    # 写入硬盘
    safe_mkdir('docs')
    safe_mkdir('docs/img')
    open(fname, 'w', encoding='utf-8').write(md)
    for name, data in imgs.items():
        open(f'docs/img/{name}', 'wb').write(data)
        
    print('已完成')
    
def summary_handle(args):
    # 读入文件列表
    fnames = [f for f in os.listdir('docs') if f.endswith('.md')]
    toc = OrderedDict()
    for fname in fnames:
        print(fname)
        md = open(path.join('docs', fname), encoding='utf8').read()
        # 提取元信息
        m = re.search(RE_YAML_META, md)
        if not m: 
            print('未找到元信息，已跳过')
            continue
        try:
            meta = yaml.safe_load(m.group(1))
        except Exception as ex: 
            print(ex)
            continue
        dt = meta.get('date', '0001-01-01 00:00:00')
        cate = meta.get('category', '未分类')
        # 提取标题
        m = re.search(RE_TITLE, md, flags=re.M)
        if not m: 
            print('未找到标题，已跳过')
            continue
        title = m.group(1)
        toc.setdefault(cate, [])
        toc[cate].append({
            'title': title,
            'file': fname,
            'date': dt,
        })
    
    # 生成目录文件
    summary = ''
    for cate, sub in toc.items():
        summary += f'+   {cate}\n'
        for art in sub:
            title = art['title']
            file = quote_plus(art['file'])
            summary += f'    +   [{title}](docs/{file})\n'
    open('SUMMARY.md', 'w', encoding='utf8').write(summary)
    
def tomd_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    for fname in fnames:
        args.fname = path.join(dir, fname)
        tomd_file(args)
    
def tomd_file(args):
    if not args.fname.endswith('.html'):
        print('请提供 HTML 文件')
        return
    print(args.fname)
    html = open(args.fname, encoding='utf8').read()
    md = tomd(html)
    ofname = re.sub(r'\.html$', '', args.fname) + '.md'
    open(ofname, 'w', encoding='utf8').write(md)

def tomd_handle(args):
    if path.isdir(args.fname):
        tomd_dir(args)
    else:
        tomd_file(args)
    
def main():
    parser = argparse.ArgumentParser(prog="BookerWikiTool", description="iBooker WIKI tool", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"BookerWikiTool version: {__version__}")
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()
    
    dl_parser = subparsers.add_parser("download", help="download a page")
    dl_parser.add_argument("url", help="url")
    dl_parser.add_argument("-e", "--encoding", default='utf-8', help="encoding")
    dl_parser.add_argument("-c", "--category", default='未分类', help="category")
    dl_parser.set_defaults(func=download_handle)
    
    sum_parser = subparsers.add_parser("summary", help="generate the summary")
    sum_parser.set_defaults(func=summary_handle)
    
    fix_parser = subparsers.add_parser("fix", help="fix titles")
    fix_parser.add_argument("file", help="file")
    fix_parser.set_defaults(func=fix_handle)
    
    acc_parser = subparsers.add_parser("account", help="account words")
    acc_parser.add_argument("file", help="file")
    acc_parser.set_defaults(func=account_handle)

    tomd_parser = subparsers.add_parser("tomd", help="html to markdown")
    tomd_parser.add_argument("file", help="file")
    tomd_parser.set_defaults(func=tomd_handle)

    bili_parser = subparsers.add_parser("dl-bili", help="download bilibili video")
    bili_parser.add_argument("id", help="av or bv")
    bili_parser.add_argument("-a", "--audio", type=bool, default=False, help="whether to convert to audio")
    bili_parser.set_defaults(func=download_bili)

    bili_kw_parser = subparsers.add_parser("dl-bili-kw", help="download bilibili video by kw")
    bili_kw_parser.add_argument("kw", help="keyword")
    bili_kw_parser.add_argument("-s", "--start", type=int, default=1, help="starting page")
    bili_kw_parser.add_argument("-e", "--end", type=int, default=10000000, help="ending page")
    bili_kw_parser.add_argument("-a", "--audio", type=bool, default=False, help="whether to convert to audio")
    bili_kw_parser.set_defaults(func=batch_kw_bili)
  
    bili_home_parser = subparsers.add_parser("dl-bili-home", help="download bilibili video by user")
    bili_home_parser.add_argument("mid", help="user id")
    bili_home_parser.add_argument("-s", "--start", type=int, default=1, help="starting page")
    bili_home_parser.add_argument("-e", "--end", type=int, default=10000000, help="ending page")
    bili_home_parser.add_argument("-a", "--audio", type=bool, default=False, help="whether to convert to audio")
    bili_home_parser.set_defaults(func=batch_home_bili)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__": main()