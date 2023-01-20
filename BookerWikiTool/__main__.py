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
from .util import *
from .epub_tool import *
from .md_tool import *
from .keyframe import *
from .fetch_links import *
from .pdf_tool import *
from .flatten import *
from .toggle_bw import *
from .crawl_wx import *
    
def main():
    parser = argparse.ArgumentParser(prog="BookerWikiTool", description="iBooker WIKI tool", formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--version", action="version", version=f"BookerWikiTool version: {__version__}")
    parser.set_defaults(func=lambda x: parser.print_help())
    subparsers = parser.add_subparsers()
    
    dl_parser = subparsers.add_parser("download", help="download a page")
    dl_parser.add_argument("url", help="url")
    dl_parser.add_argument("-e", "--encoding", default='utf-8', help="encoding")
    dl_parser.add_argument("-c", "--category", default='未分类', help="category")
    dl_parser.add_argument("-t", "--title", default='title', help="selector of article title")
    dl_parser.add_argument("-b", "--body", default='', help="selector of article body")
    dl_parser.set_defaults(func=download_handle)
    
    wiki_sum_parser = subparsers.add_parser("wiki-summary", help="generate wiki summary")
    wiki_sum_parser.set_defaults(func=wiki_summary_handle)
    
    summary_parser = subparsers.add_parser("summary", help="generate summary")
    summary_parser.add_argument("dir", help="dir")
    summary_parser.set_defaults(func=summary_handle)
    
    ren_parser = subparsers.add_parser("ren-md", help="rename md fname")
    ren_parser.add_argument("fname", help="file for dir name")
    ren_parser.add_argument("-t", "--threads", type=int, default=8, help="num of threads")
    ren_parser.add_argument("-b", "--by", type=str, choices=['title', 'src'], default='src', help="where to extract fname")
    ren_parser.set_defaults(func=ren_md_handle)
    
    acc_parser = subparsers.add_parser("account", help="account words")
    acc_parser.add_argument("file", help="file")
    acc_parser.set_defaults(func=account_handle)

    tomd_parser = subparsers.add_parser("tomd", help="html to markdown")
    tomd_parser.add_argument("fname", help="file or dir name")
    tomd_parser.add_argument("-t", "--threads", type=int, default=8, help="num of threads")
    tomd_parser.set_defaults(func=tomd_handle)

    office2pdf_parser = subparsers.add_parser("office2pdf", help="doc/xls/ppt to pdf")
    office2pdf_parser.add_argument("fname", help="file name")
    office2pdf_parser.set_defaults(func=office2pdf_handle)

    fmtzh_parser = subparsers.add_parser("fmtzh", help="format zh")
    fmtzh_parser.add_argument("fname", help="file name")
    fmtzh_parser.set_defaults(func=fmt_zh_handle)

    opti_md_parser = subparsers.add_parser("opti-md", help="optimize markdown")
    opti_md_parser.add_argument("fname", help="file name")
    opti_md_parser.add_argument("-t", "--threads", type=int, default=8, help="num of threads")
    opti_md_parser.set_defaults(func=opti_md_handle)

    flatten_parser = subparsers.add_parser("flatten", help="flatten dir")
    flatten_parser.add_argument("dir", help="dir name")
    flatten_parser.add_argument("-d", "--delim", default='：', help="delimiter")
    flatten_parser.set_defaults(func=flatten_dir)

    comp_epub_parser = subparsers.add_parser("comp-epub", help="compress epub")
    comp_epub_parser.add_argument("file", help="file")
    comp_epub_parser.set_defaults(func=comp_epub)

    epub_toc_parser = subparsers.add_parser("epub-toc", help="view epub toc")
    epub_toc_parser.add_argument("fname", help="fname")
    epub_toc_parser.set_defaults(func=get_epub_toc)

    epub_chs_parser = subparsers.add_parser("epub-chs", help="export epub chapters")
    epub_chs_parser.add_argument("fname", help="fname")
    epub_chs_parser.add_argument("-d", "--dir", default='.', help="output dir")
    epub_chs_parser.add_argument("-s", "--start", default=-1, type=int, help="starting index. -1 means all")
    epub_chs_parser.add_argument("-e", "--end", default=-1, type=int, help="ending index. -1 means all")
    epub_chs_parser.add_argument("-r", "--regex", required=True, help="regex for chapter title")
    epub_chs_parser.set_defaults(func=exp_epub_chs)

    kf_parser = subparsers.add_parser("ext-kf", help="extract keyframes")
    kf_parser.add_argument("file", help="file")
    kf_parser.add_argument("--save-path", default='out', help="path to save")
    kf_parser.set_defaults(func=ext_keyframe)

    ext_pdf_parser = subparsers.add_parser("ext-pdf", help="extract odf into images")
    ext_pdf_parser.add_argument("fname", help="file name")
    ext_pdf_parser.add_argument("-d", "--dir", default='.', help="path to save")
    ext_pdf_parser.add_argument("-w", "--whole", action='store_true', default=False, help="whether to clip the whole page")
    ext_pdf_parser.set_defaults(func=ext_pdf)

    waifu2x_auto_parser = subparsers.add_parser("waifu2x-auto", help="process imgs with waifu2x")
    waifu2x_auto_parser.add_argument("fname", help="file or dir name")
    waifu2x_auto_parser.add_argument("-t", "--threads", help="num of threads", type=int, default=8)
    waifu2x_auto_parser.set_defaults(func=waifu2x_auto_handle)

    pack_pdf_parser = subparsers.add_parser("pack-pdf", help="package images into pdf")
    pack_pdf_parser.add_argument("dir", help="dir name")
    pack_pdf_parser.add_argument("-r", "--regex", help="regex of keyword for grouping")
    pack_pdf_parser.set_defaults(func=pack_pdf)

    fetch_links_parser = subparsers.add_parser("fetch-links", help="fetch links in pages")
    fetch_links_parser.add_argument("url", help="url with {i} as page num")
    fetch_links_parser.add_argument("link", help="link selector")
    fetch_links_parser.add_argument("ofname", help="output file name")
    fetch_links_parser.add_argument("-s", "--start", type=int, default=1, help="starting page")
    fetch_links_parser.add_argument("-e", "--end", type=int, default=10000000, help="ending page")
    fetch_links_parser.add_argument("-p", "--proxy", help="proxy")
    fetch_links_parser.add_argument("-H", "--headers", help="headers in JSON")
    fetch_links_parser.set_defaults(func=fetch_links)

    toggle_bw_parser = subparsers.add_parser("tog-bw", help="check if image colors reversed and then toggle them")
    toggle_bw_parser.add_argument("fname", help="file or dir name")
    toggle_bw_parser.add_argument("-t", "--threads", type=int, default=8, help="num of thread")
    toggle_bw_parser.add_argument("-s", "--thres", type=int, default=50, help="threshold less than which the color will be regarded as black")
    toggle_bw_parser.set_defaults(func=toggle_bw_handle)

    config_proj_parser = subparsers.add_parser("config-proj", help="config proj")
    config_proj_parser.add_argument("dir", help="dir name")
    config_proj_parser.set_defaults(func=config_proj)

    crawl_wx_parser = subparsers.add_parser("crawl-wx", help="crawler weixin articles")
    crawl_wx_parser.add_argument("fname", help="XLSX fname")
    crawl_wx_parser.add_argument("-n", "--size", type=int, default=500, help="num of articles per ebook")
    crawl_wx_parser.set_defaults(func=crawl_wx)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__": main()