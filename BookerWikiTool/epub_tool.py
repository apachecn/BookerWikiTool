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
        
def get_ncx_toc(toc_ncx):
    toc_ncx = re.sub(r'<\?xml[^>]*\?>', '', toc_ncx)
    toc_ncx = re.sub(r'xmlns=".+?"', '', toc_ncx)
    toc_ncx = re.sub(r'<(/?)navLabel', r'<\1label', toc_ncx)
    toc_ncx = re.sub(r'<(/?)navPoint', r'<\1nav', toc_ncx)
    # print(toc_ncx)
    rt = pq(toc_ncx)
    el_nps = rt('nav')
    toc = []
    for i in range(len(el_nps)):
        el = el_nps.eq(i)
        title = el.children('label>text').text()
        src = el.children('content').attr('src')
        toc.append([i, title, src])
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
    for i, title, src in toc:
        print(i, title, src)

def exp_epub_chs(args):
    fname = args.fname
    rgx = args.regex
    st = args.start
    ed = args.end
    dir = args.dir
    
    if not fname.endswith('.epub'):
        print('请提供 EPUB 文件')
        return
        
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    toc_ncx = zip.read('OEBPS/toc.ncx').decode('utf8')
    toc = get_ncx_toc(toc_ncx)
    if ed != -1: toc = toc[:ed+1]
    if st != -1: toc = toc[st:]
    
    chs = []
    ch = None
    for i, title, src in toc:
        if re.search(rgx, title.strip()):
            ch = []
            chs.append(ch)
        if ch is not None:
            ch.append(src)
            
    l = len(str(len(chs)))
    for i, ch in enumerate(chs):
        conts = []
        for sec in ch:
            cont = zip.read(f'OEBPS/{sec}').decode('utf8')
            cont = pq(cont).find('body').eq(0).text()
            conts.append(cont)
        cont = '\n'.join(conts)
        cont = f'<html><head></head><body>{cont}</body></html>'
        
        fname = path.join(dir, str(i).zfill(l) + '.html')
        open(fname, 'w', encoding='utf8').write(cont)
        
def exp_epub_chs(args):
    fname = args.fname
    rgx = args.re
    st = args.start
    ed = args.end
    dir = args.dir
    
        if not fname.endswith('.epub'):
        print('请提供 EPUB 文件')
        return
        
    bio = BytesIO(open(fname, 'rb').read())
    zip = zipfile.ZipFile(bio, 'r', zipfile.ZIP_DEFLATED)
    toc_ncx = zip.read('OEBPS/toc.ncx').decode('utf8')
    toc = get_ncx_toc(toc_ncx)
    if ed != -1: toc = toc[:ed+1]
    if st != -1: toc = toc[st:]
    
    chs = []
    ch = None
    for i, title, src in toc:
        if re.search(rgx, title.strip()):
            ch = []
            chs.append(ch)
        if ch is not None:
            ch.append(src)
            
    l = len(str(len(chs)))
    for i, ch in enumerate(chs):
        conts = []
        for sec in ch:
            cont = zip.read(f'OEBPS/{sec}').decode('utf8')
            cont = pq(cont).find('body').eq(0).text()
            conts.append(cont)
        cont = '\n'.join(conts)
        cont = f'<html><head></head><body>{cont}</body></html>'
        
        fname = path.join(dir, str(i).zfill(l) + '.html')
        open(fname, 'w', encoding='utf8').write(cont)
