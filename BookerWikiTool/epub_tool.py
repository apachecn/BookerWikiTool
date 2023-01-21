from io import BytesIO
import zipfile
from os import path
from imgyaso import pngquant_bts
import sys
from EpubCrawler.util import is_pic, safe_mkdir, safe_rmdir
import subprocess as subp
from pyquery import PyQuery as pq
import re

def convert_to_epub(fname):
    nfname = re.sub(r'\.\w+$', '', fname) + '.epub'
    print(f'{fname} => {nfname}')
    subp.Popen(f'ebook-convert "{fname}" "{nfname}"', 
        shell=True, stdin=subp.PIPE, stdout=subp.PIPE).communicate()
    if not path.exists(nfname):
        raise FileNotFoundError(f'{nfname} not found')
    return nfname

def comp_epub(args):
    fname = args.file
    if fname.endswith('.mobi') or \
        fname.endswith('.azw3'):
            fname = convert_to_epub(fname)
    elif not fname.endswith('.epub'):
        print('请提供EPUB')
        return
        
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    new_bio = BytesIO()
    new_zip = zipfile.ZipFile(new_bio, 'w', zipfile.ZIP_DEFLATED)
    
    for n in zip.namelist():
        print(n)
        data = zip.read(n)
        if is_pic(n):
            data = pngquant_bts(data)
        new_zip.writestr(n, data)
        
    zip.close()
    new_zip.close()
    open(fname, 'wb').write(new_bio.getvalue())
    print('done...')
        
        
def get_opf_flist(cont_opf):
    cont_opf = re.sub(r'<\?xml[^>]*\?>', '', cont_opf)
    cont_opf = re.sub(r'xmlns=".+?"', '', cont_opf)
    rt = pq(toc_ncx)
    el_irs = rt('itemref')
    ids = [
        el_irs.eq(i).attr('idref') 
        for i in range(len(el_irs))
    ]
    el_its = rt('item')
    id_map = {
        pq(el).attr('id'):
        pq(el).attr('href')
        for el in el_irs
    }
    return [
        id_map[id]
        for id in ids
        if id in id_map
    ]

def get_toc_lv(el_nav):
    cnt = 0
    while el_nav and el_nav.is_('nav'):
        cnt += 1
        el_nav = el_nav.parent()
    return cnt

def get_ncx_toc(toc_ncx):
    toc_ncx = re.sub(r'<\?xml[^>]*\?>', '', toc_ncx)
    toc_ncx = re.sub(r'xmlns=".+?"', '', toc_ncx)
    toc_ncx = re.sub(r'<(/?)navLabel', r'<\1label', toc_ncx)
    toc_ncx = re.sub(r'<(/?)navPoint', r'<\1nav', toc_ncx)
    toc_ncx = re.sub(r'<(/?)navmap', r'<\1map', toc_ncx)
    rt = pq(toc_ncx)
    el_nps = rt('nav')
    toc = []
    for i in range(len(el_nps)):
        el = el_nps.eq(i)
        title = el.children('label>text').text()
        src = el.children('content').attr('src')
        toc.append({
            'idx': i,
            'title': title.strip(),
            'src': src,
            'level': get_toc_lv(el),
        })
    return toc

def get_epub_toc(args):
    fname = args.fname
    if not fname.endswith('.epub'):
        print('请提供 EPUB 文件')
        return
        
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    toc_ncx = zip.read('OEBPS/toc.ncx').decode('utf8')
    toc = get_ncx_toc(toc_ncx)
    for ch in toc:
        pref = '>' * (ch["level"] - 1)
        if pref: pref += ' '
        print(f'{pref}{ch["idx"]}：{ch["src"]}\n{pref}{ch["title"]}')

def exp_epub_chs(args):
    fname = args.fname
    rgx = args.regex
    hlv = args.hlevel
    st = args.start
    ed = args.end
    dir = args.dir
    
    if not fname.endswith('.epub'):
        print('请提供 EPUB 文件')
        return
        
    # 获取目录和文件列表
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    toc_ncx = zip.read('OEBPS/toc.ncx').decode('utf8')
    cont_opf = zip.read('OEBPS/content.opf').decode('utf8')
    toc = get_ncx_toc(toc_ncx)
    flist = get_opf_flist(cont_opf)
    
    # 过滤目录
    if rgx:
        toc = [
            ch for ch in toc 
            if re.search(rgx, ch['title'])
        ]
    if hlv:
        toc = [
            ch for ch in toc 
            if ch['level'] <= hlv
        ]
    toc_flist = {
        re.sub(r'#.+$|\?.+$', '', ch['src']) 
        for ch in toc
    }
    
    # 按照目录合并文件
    chs = []
    for f in flist:
        cont = zip.read(f).decode('utf8')
        if f in toc_flist:
            chs.appen([cont])
        else:
            if chs: chs[-1].append(cont)
    chs = ['\n'.join(ch) for ch in chs]
    chs = [
        f'<html><head></head><body>{ch}</body></html>' 
        for ch in chs
    ]
    l = len(str(len(chs)))
    for i, ch in enumerate(chs):
        fname = path.join(dir, str(i).zfill(l) + '.html')
        open(fname, 'w', encoding='utf8').write(ch)