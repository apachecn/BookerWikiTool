import sys
from urllib.parse import urljoin
from EpubCrawler.util import request_retry
from pyquery import PyQuery as pq
import json
import re
import subprocess as subp
from .util import *

config = {
    'url': '',
    'link': '',
    'time': '',
    'proxy': None,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    },
}

def get_toc(html, base, re_tm):
    root = pq(html)
    el_links = root(config['link'])
    el_times = None
    if config['time']:
        el_times = root(config['time'])
        assert len(el_links) == len(el_times)
    links = []
    for i in range(len(el_links)):
        url = el_links.eq(i).attr('href')
        if not url:
            links.append(el_links.eq(i).text().strip())
            continue
        url = urljoin(base, url)
        if el_times:
            tm = el_times.eq(i).text().strip()
            m = re.search(re_tm, tm)
            url += '#' + (m.group() if m else tm)
        links.append(url)
    return links

def fetch_links(args):
    config['url'] = args.url
    config['link'] = args.link
    config['time'] = args.time
    ofname = args.ofname
    st = args.start
    ed = args.end
    
    if args.proxy:
        config['proxy'] = {
            'http': args.proxy,
            'https': args.proxy,
        }
    if args.headers:
        config['headers'] = json.loads(args.headers)
    
    ofile = open(ofname, 'a', encoding='utf-8')
    
    for i in range(st, ed + 1):
        url = config['url'].replace('{i}', str(i))
        print(url)
        html = request_retry(
            'GET', url, 
            proxies=config['proxy'],
            headers=config['headers'],
        ).text
        toc = get_toc(html, url, args.time_regex)
        if len(toc) == 0: break
        for it in toc:
            print(it)
            ofile.write(it + '\n')
    
    ofile.close()

def time_match_to_str(m):
    yr = m.group(1)
    mon = m.group(2)
    if len(mon) == 1: mon = '0' + mon
    return yr + mon

def batch_links(args):
    num = args.num
    links = open(args.links, encoding='utf8').read().split('\n')
    links = list(filter(None, links))
    
    dates = [re.search('#' + args.time_regex, l) for l in links]
    if not all(dates):
        print('未能提取文章发布时间')
        return
    
    for i in range(0, len(links), args.num):
        st = time_match_to_str(dates[i])
        ed = time_match_to_str(dates[min(len(dates)-1, i+num)])
        if st > ed: st, ed = ed, st
        
        cfg = {
            'name': f'{args.name} {st}-{ed}',
            'url': links[i],
            'title': args.title,
            'content': args.content,
            'remove': args.remove,
            'optiMode': args.opti_mode,
            'list': links[i:i+args.num],
        }

        cfg_fname = f'config_{fname_escape(args.name)}_{st}_{ed}.json'
        open(cfg_fname, 'w', encoding='utf8').write(json.dumps(cfg))
        subp.Popen(['crawl-epub', cfg_fname], shell=True).communicate()
        