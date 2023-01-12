import tempfile
import uuid
import subprocess as subp
import re
import os
import shutil
import json
import yaml
from urllib.parse import quote_plus
from os import path
from pyquery import PyQuery as pq
from datetime import datetime
from collections import OrderedDict

RE_YAML_META = r'<!--yml([\s\S]+?)-->'
RE_TITLE = r'^#+ (.+?)$'
RE_SOURCE = r'/([^/\n]+?)/?>'
RE_CODE_BLOCK = r'```[\s\S]+?```'
RE_IMG = r'!\[.*?\]\(.*?\)'
# Word 字数统计标准：
# 一个汉字或中文标点算一个字
# 一个连续的英文字母、标点和数字序列算一个字
RE_ZH_WORD = r'[\u2018-\u201d\u3001-\u301c\u4e00-\u9fff\uff01-\uff65]'
RE_EN_WORD = r'[\x21-\x7e]+'
RE_IFRAME = r'<iframe[^>]*src="(.+?)"[^>]*>'
RE_IFRAME_ALL = r'</?iframe[^>]*>'
RE_IFRAME_REPL = r'<br/><br/><a href="\1">\1</a><br/><br/>'
RE_SRC_FULL = r'原文:\[.+?\]\((.+?)\)'
RE_SRC_FULL_REP = r'原文：<\1>'
RE_PRE_HEAD = r'^\x20*\*+\x20*```'
RE_LEG_TOKEN = r'T\d+】'

DIR = path.dirname(path.abspath(__file__))

default_hdrs = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
}

headers = {
    'User-Agent': 'PostmanRuntime/7.26.8',
    'Referer': 'https://www.bilibili.com/',
}


def d(name):
    return path.join(DIR, name)

def tomd(html):
    # 处理 IFRAME
    html = re.sub(RE_IFRAME, RE_IFRAME_REPL, html)
    html = re.sub(RE_IFRAME_ALL, '', html)
    js_fname = d('tomd.js')
    html_fname = path.join(tempfile.gettempdir(), uuid.uuid4().hex + '.html')
    open(html_fname, 'w', encoding='utf8').write(html)
    subp.Popen(
        ["node", js_fname, html_fname],
        shell=True,
    ).communicate()
    md_fname = re.sub(r'\.html$', '', html_fname) + '.md'
    md = open(md_fname, encoding='utf8').read()
    os.remove(html_fname)
    return md

def fname_escape(name):
    return name.replace('\\', '＼') \
               .replace('/', '／') \
               .replace(':', '：') \
               .replace('*', '＊') \
               .replace('?', '？') \
               .replace('"', '＂') \
               .replace('<', '＜') \
               .replace('>', '＞') \
               .replace('|', '｜')
               
def account_words(cont):
    # 去掉代码块和图片
    cont = re.sub(RE_CODE_BLOCK, '', cont)
    cont = re.sub(RE_IMG, '', cont)
    zh_count = len(re.findall(RE_ZH_WORD, cont))
    en_count = len(re.findall(RE_EN_WORD, cont))
    total = zh_count + en_count
    return (total, zh_count, en_count)
    
def fmt_zh(text):
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9_])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9_])([\u4e00-\u9fff])', r'\1 \2', text)
    return text
    
def safe_mkdir(dir):
    try: os.mkdir(dir)
    except: pass
    
def safe_rmdir(dir):
    try: shutil.rmtree(dir)
    except: pass

def is_pic(fname):
    ext = [
        'jpg', 'jpeg', 'jfif', 'png', 
        'gif', 'tiff', 'webp'
    ]
    m = re.search(r'\.(\w+)$', fname)
    return bool(m and m.group(1) in ext)

def find_cmd_path(name):
    for p in os.environ.get('PATH', '').split(';'):
        if path.isfile(path.join(p, name)) or \
            path.isfile(path.join(p, name + '.exe')):
            return p
    return ''
    
def is_video(fname):
    ext = [
        'mp4', 'm4v', '3gp', 'mpg', 'flv', 'f4v', 
        'swf', 'avi', 'gif', 'wmv', 'rmvb', 'mov', 
        'mts', 'm2t', 'webm', 'ogg', 'mkv', 'mp3', 
        'aac', 'ape', 'flac', 'wav', 'wma', 'amr', 'mid',
    ]
    m = re.search(r'\.(\w+)$', fname)
    return bool(m and m.group(1) in ext)