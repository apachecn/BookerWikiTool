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

def get_toc_json(jstr, re_tm):
    j = json.loads(jstr)
    links = dict_get_recur(j, config['link'])
    times = None
    if config['time']:
        times = dict_get_recur(j, config['time'])
        assert len(links) == len(times)
        for i, t in enumerate(times):
            m = re.search(re_tm, t)
            times[i] = m.group() if m else t
        links = [f'{l}#{t}' for l, t in zip(links,times)]
    return links
    

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
        if args.json:
            toc = get_toc_json(html, args.time_regex)
        else:
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
        ed = time_match_to_str(dates[i:i+args.num][-1])
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
        print(cfg_fname)
        if args.exec:
            subp.Popen(['crawl-epub', cfg_fname], shell=True).communicate()
        
        
def fetch_sitemap_handle(args):
    url, regex, ofname = args.url, args.regex, args.ofname
    urls = fetch_sitemap(url, regex)
    f = open(ofname, 'w', encoding='utf8')
    for u in urls:
        f.write(u + '\n')
        print(u)
    f.close()

        
def fetch_sitemap(url, rgx):
    xml = request_retry('GET', url).text
    xml = re.sub(r'<\?xml[^>]*>', '', xml)
    xml = re.sub(r'xmlns=".+?"', '', xml)
    rt = pq(xml)
    urls = []
    subs = [
        pq(el).text() for el in rt('loc') 
        if pq(el).text().endswith('.xml')
    ]
    for s in subs:
        urls += fetch_sitemap(s, rgx)
    el_urls = pq([
        el for el in rt('url') 
        if not pq(el).children('loc').text().endswith('.xml')
           and re.search(rgx, pq(el).children('loc').text()) 
    ])
    urls += [
        pq(el).children('loc').text() + '#' +
        (pq(el).children('lastmod').text() or '0001-01-01') 
        for el in el_urls
    ]
    return urls

    