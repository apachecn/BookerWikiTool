import fitz
import win32com.client
import subprocess as subp
import sys
from os import path
import re
import os
import copy
import traceback
from PIL import Image, ImageFile
from multiprocessing import Pool
import img2pdf
from .util import *

ImageFile.LOAD_TRUNCATED_IMAGES = True

def ext_pdf(args):
    if path.isdir(args.fname):
        ext_pdf_dir(args)
    else:
        ext_pdf_file(args)

def ext_pdf_dir(args):
    dir = args.fname
    for fname in os.listdir(dir):
        try:
            ffname = path.join(dir, fname)
            args.fname = ffname
            ext_pdf_file(args)
        except: traceback.print_exc()

def ext_pdf_file(args):
    fname, dir = args.fname, args.dir
    if not fname.endswith('.pdf'):
        print('请提供 PDF 文件')
        return
    print(f'file: {fname}')
    title = path.basename(fname)[:-4]

    doc = fitz.open(fname)
    lp = len(str(len(doc)))
    for ip, p in enumerate(doc):
        print(f'page: {ip + 1}')
        
        # 判断是否整页截图
        if args.whole:
            img = p.get_pixmap()
            imgname = path.join(dir, f'{title}_{ip+1:0{lp}d}.png')
            print(f'save: {imgname}')
            img.writePNG(imgname)
            continue
        
        imgs = p.get_images()
        limg = len(str(len(imgs)))
        for ii, info in enumerate(imgs):
            xref = info[0]
            print(f'img: {ii + 1}, xref: {xref}')
            img = fitz.Pixmap(doc, xref)
            if img.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            imgname = path.join(dir, f'{title}_{ip+1:0{lp}d}_{ii+1:0{limg}d}.png')
            print(f'save: {imgname}')
            img.writePNG(imgname)
    
    doc.close()

def get_scale_by_width(wid):
    if wid < 800:
        return 4
    elif wid < 900:
        return 3.5
    elif wid < 1000:
        return 3
    elif wid < 1200:
        return 2.5
    elif wid < 1600:
        return 2
    elif wid < 2000:
        return 1.5
    elif wid < 3200:
        return 1
    elif wid < 4200:
        return 0.75
    else:
        return 0.5

def pack_pdf(args):
    dir, rgx = args.dir, args.regex
    if dir.endswith('/') or \
        dir.endswith('\\'):
        dir = dir[:-1]
    
    fnames = filter(is_pic, os.listdir(dir))
    if not rgx:
        fnames = [path.join(dir, f) for f in fnames]
        pdf = img2pdf.convert(fnames)
        fname = dir + '.pdf'
        print(fname)
        open(fname, 'wb').write(pdf)
        return
        
    d = {}
    for fname in fnames:
        m = re.search(rgx, fname)
        if not m: continue
        kw = m.group(0)
        d.setdefault(kw, [])
        d[kw].append(fname)
        
    for kw, fnames in d.items():
        fnames = [path.join(dir, f) for f in fnames]
        pdf = img2pdf.convert(fnames)
        fname = path.join(dir, kw + '.pdf')
        print(fname)
        open(fname, 'wb').write(pdf)

def ppt2pdf(fname, ofname):
    app = win32com.client.Dispatch('PowerPoint.Application')
    ppt = app.Presentations.Open(fname)
    ppt.SaveAs(ofname, 32)
    app.Quit()
    
def ppt2pdf_file(args):
    fname = args.fname
    print(fname)
    if not fname.endswith('.ppt') and \
        not fname.endswith('.pptx'):
            print('请提供 PPT 文件')
            return
    fname = path.join(os.getcwd(), fname)
    ofname = fname.replace('.ppt', '') \
        .replace('.pptx', '') + '.pdf'
    ofname = path.join(os.getcwd(), ofname)
    ppt2pdf(fname, ofname)
    print("转换成功！")

def ppt2pdf_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    for f in fnames:
        ff = path.join(dir, f)
        args.fname = ff
        try: ppt2pdf_file(args)
        except Exception as ex: print(ex)

def waifu2x_auto_file_safe(args):
    try: waifu2x_auto_file(args)
    except Exception as ex: print(ex)

def waifu2x_auto_file(args):
    fname = args.fname
    if not is_pic(fname):
        print('请提供图像')
        return
    print(fname)
    try: img = Image.open(fname)
    except: 
        print('文件无法打开')
        return
    width = min(img.size[0], img.size[1])
    scale = get_scale_by_width(width)
    img.close()
    p = find_cmd_path('waifu2x-converter-cpp')
    cmd = [
        'waifu2x-converter-cpp', 
        '-m', 'noise-scale',
        '--noise-level', '2',
        '--scale-ratio', str(scale),
        '--block-size', '256',
        '-i', fname,
        '-o', fname,
        '--model-dir', path.join(p, 'models_rgb'),
        '--disable-gpu',
    ]
    print(f'cmd: {cmd}')
    r = subp.Popen(
        cmd, 
        shell=True,
        stdout=subp.PIPE,
        stderr=subp.PIPE,
    ).communicate()
    open(fname, 'ab').close() # touch
    print(r[0].decode('utf8', 'ignore') or 
        r[1].decode('utf8', 'ignore'))

def waifu2x_auto_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    pool = Pool(args.threads)
    for f in fnames:
        ff = path.join(dir, f)
        args = copy.deepcopy(args)
        args.fname = ff
        pool.apply_async(waifu2x_auto_file_safe, [args])
    pool.close()
    pool.join()
    
def waifu2x_auto_handle(args):
    # 检查 waifu2x
    r = subp.Popen(
        ['waifu2x-converter-cpp', '--version'],
        shell=True,
        stdout=subp.PIPE,
        stderr=subp.PIPE,
    ).communicate()
    if r[1]: 
        print('waifu2x-converter-cpp 未找到，请下载并将其目录添加到系统变量 PATH 中')
        return
    if path.isdir(args.fname):
        waifu2x_auto_dir(args)
    else:
        waifu2x_auto_file(args)
        
def ppt2pdf_handle(args):
    if path.isdir(args.fname):
        ppt2pdf_dir(args)
    else:
        ppt2pdf_file(args)
