import argparse
import requests
from readability import Document
import tempfile
import uuid
import subprocess as subp
import re
import os
import shutil
import json
import yaml
import traceback
import copy
from multiprocessing import Pool
from urllib.parse import quote_plus
from os import path
from pyquery import PyQuery as pq
from datetime import datetime
from collections import OrderedDict
from EpubCrawler.img import process_img
from EpubCrawler.util import safe_mkdir
from .util import *
from .fmt import *

def account_handle(args):
    if not args.file.endswith('.md'):
        print('请提供 markdown 文件')
        return
    print(args.file)
    cont = open(args.file, encoding='utf8').read()
    total, zh_count, en_count = account_words(cont)
    print(f'中文字数：{zh_count}\n英文字数：{en_count}\n总字数：{total}')

def ren_md_handle(args):
    if path.isdir(args.fname):
        ren_md_dir(args)
    else:
        ren_md_file(args)

def ren_md_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    pool = Pool(args.threads)
    for f in fnames:
        args = copy.deepcopy(args)
        args.fname = path.join(dir, f)
        pool.apply_async(ren_md_file_safe, [args])
    pool.close()
    pool.join()

def ren_md_file_safe(args):
    try: ren_md_file(args)
    except: traceback.print_exc()

def ren_md_file(args):
    fname = args.fname
    if not fname.endswith('.md'):
        print('请提供 markdown 文件')
        return
    cont = open(fname, encoding='utf8').read()
    dir = path.dirname(fname)
    RE = RE_SOURCE if args.by == 'src' else RE_TITLE
    rm = re.search(RE, cont, flags=re.M)
    if not rm: 
        print(f'{fname} 未找到文件名')
        return
    nfname = rm.group(1)
    nfname = re.sub(r'\s', '-', fname_escape(nfname)) + '.md'
    nfname = path.join(dir, nfname)
    print(nfname)
    shutil.move(fname, nfname)

def download_handle(args):
    html = requests.get(
        args.url,
        headers=default_hdrs,
    ).content.decode(args.encoding, 'ignore')
    
    # 解析标题
    rt = pq(html)
    el_title = rt.find(args.title).eq(0)
    title = el_title.text().strip()
    el_title.remove()
    
    # 判断是否重复
    title_esc = re.sub(r'\s', '-', fname_escape(title))
    fname = f'docs/{title_esc}.md'
    if path.isfile(fname):
        print(f'{title} 已存在')
        return
    
    # 解析内容并下载图片
    if args.body:
        co = rt.find(args.body).html()
    else:
        co = Document(str(rt)).summary()
        co = pq(co).find('body').html()
    if not co: 
        print('未获取到内容！')
        return 
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
    dir = args.dir
    fnames = [f for f in os.listdir(dir) if f.endswith('.md')]
    toc = []
    for f in fnames:
        fullf = path.join(dir, f)
        print(fullf)
        cont = open(fullf, encoding='utf8').read()
        m = re.search(RE_TITLE, cont, flags=re.M)
        if not m: continue
        title = m.group(1)
        toc.append(f'+   [{title}]({f})')
    summary = '\n'.join(toc)
    open(path.join(dir, 'SUMMARY.md'), 'w', encoding='utf8').write(summary)
    
def wiki_summary_handle(args):
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
            traceback.print_exc()
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
    pool = Pool(args.threads)
    for fname in fnames:
        args = copy.deepcopy(args)
        args.fname = path.join(dir, fname)
        # tomd_file(args)
        pool.apply_async(tomd_file_safe, [args])
    pool.close()
    pool.join()

def tomd_file_safe(args):
    try: tomd_file(args)
    except: traceback.print_exc()

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

def fmt_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    pool = Pool(args.threads)
    for fname in fnames:
        args = copy.deepcopy(args)
        args.fname = path.join(dir, fname)
        pool.apply_async(fmt_file_safe, [args])
    pool.close()
    pool.join()
    
def fmt_file_safe(args):
    try: fmt_file(args)
    except: traceback.print_exc()
    
def fmt_file(args):
    mode = args.mode
    if not args.fname.endswith('.html') and \
        not args.fname.endswith('.md'):
        print('请提供 HTML 或 MD 文件')
        return
    print(args.fname)
    text = open(args.fname, encoding='utf8').read()
    if mode == 'zh':
        text = fmt_zh(text)
    elif mode == 'packt':
        text = fmt_packt(text)
    open(args.fname, 'w', encoding='utf8').write(text)

def fmt_handle(args):
    if path.isdir(args.fname):
        fmt_dir(args)
    else:
        fmt_file(args)

def opti_md_file_safe(args):
    try: opti_md_file(args)
    except: traceback.print_exc()

def opti_md_file(args):
    RE_SRC_FULL = r'原文[:：]\[.+?\]\((.+?)\)'
    RE_SRC_FULL_REP = r'原文：<\1>'
    RE_PRE_HEAD = r'^\x20*\*+\x20*```'
    RE_LEG_TOKEN = r'T\d+】'
    RE_PRE_HEAD2 = r'```\*+|\*+```'
    fname = args.fname
    if not fname.endswith('.md'):
        print('请提供 Markdown 文件')
        return
    print(fname)
    cont = open(fname, encoding='utf8').read()
    cont = cont.replace('../Images/', 'img/')
    cont = re.sub(RE_LEG_TOKEN, '', cont)
    cont = re.sub(RE_SRC_FULL, RE_SRC_FULL_REP, cont)
    cont = re.sub(r'#\d+\-\d+\-\d+(?=>)', '', cont)
    cont = re.sub(RE_PRE_HEAD, '```', cont, flags=re.M)
    cont = re.sub(RE_PRE_HEAD2, '```', cont)
    open(fname, 'w', encoding='utf8').write(cont)
   


def opti_md_handle(args):
    if path.isdir(args.fname):
        opti_md_dir(args)
    else:
        opti_md_file(args)

def opti_md_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    pool = Pool(args.threads)
    for fname in fnames:
        args = copy.deepcopy(args)
        args.fname = path.join(dir, fname)
        # tomd_file(args)
        pool.apply_async(opti_md_file_safe, [args])
    pool.close()
    pool.join()


def config_proj(args):
    dir = path.abspath(args.dir)
    if not path.isdir(dir):
        print('请提供目录')
        return
    fnames = os.listdir(dir)
    if 'README.md' not in fnames or \
        'index.html' not in fnames or \
        'CNAME' not in fnames:
        print('缺少 README.md，index.html 或 CNAME 文件')
        return
    name = input('请输入中文名称：').strip() or '{name}'
    name_en = input('请输入英文名称：').strip() or '{nameEn}'
    url_en = input('请输入英文链接：').strip() or '{urlEn}'
    domain = input('请输入域名前缀：').strip() or '{domain}'
    color = input('请输入颜色：').strip() or '{color}'
    repo = path.basename(dir)
    
    conts = {
        'README.md': open(path.join(dir, 'README.md'), encoding='utf8').read(),
        'index.html': open(path.join(dir, 'index.html'), encoding='utf8').read(),
        'CNAME': open(path.join(dir, 'CNAME'), encoding='utf8').read(),
    }
    for fname, cont in conts.items():
        cont = (
            cont.replace('{name}', name)
                .replace('{nameEn}', name_en)
                .replace('{urlEn}', url_en)
                .replace('{urlEn}', url_en)
                .replace('{domain}', domain)
                .replace('{color}', color)
                .replace('{adminName}', '飞龙')
                .replace('{adminUn}', 'wizardforcel')
                .replace('{adminQq}', '562826179')
                .replace('{repo}', repo)
                .replace('{dockerName}', repo)
                .replace('{pypiName}', repo)
                .replace('{npmName}', repo)
        )
        open(path.join(dir, fname), 'w', encoding='utf8').write(cont)

def convert_cdrive_log(args):
    RE_INFO = r'\[(.+?)\]([^\[]+)'
    RE_TITLE = r'上传: (.+?) \([\d\.]+ \w+\)\n'
    RE_META = r'META URL -> (\S+)'
    
    fname = args.fname
    co = open(fname, encoding='utf8').read()
    cos = co.split(' 上传: ')
    res = ['| 文件 | 链接 |\n| --- | --- |\n']
    for info in cos:
        info = ' 上传: ' + info
        title = re.search(RE_TITLE, info)
        meta = re.search(RE_META, info)
        if not title: continue
        title = title.group(1)
        meta = meta.group(1) if meta else '未上传'
        res.append(f'| {title} | {meta} |\n')
        
    res = ''.join(res)
    open(fname + '.md', 'w', encoding='utf8').write(res)
