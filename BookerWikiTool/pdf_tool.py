import fitz
from os import path
import re
import os
import traceback
from PIL import Image
from .util import *

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
    if wid < 700:
        return 'x4'
    elif wid < 1000:
        return 'x3'
    elif wid < 1800:
        return 'x2'
    elif wid < 3200:
        return 'x1'
    elif wid < 4000:
        return 'x0.75'
    else:
        return 'x0.5'

def select_img(args):
    dir = args.dir
    if not path.isdir(dir):
        print('请提供目录')
        return
    fnames = os.listdir(dir)
        
    for fname in fnames:
        print(fname)
        if not is_pic(fname): continue
        ffname = path.join(dir, fname)
        img = Image.open(ffname)
        scale = get_scale_by_width(img.size[0])
        img.close()
        safe_mkdir(path.join(dir, scale))
        os.rename(ffname, path.join(dir, scale, fname))
