import numpy as np
import cv2
import traceback
import os
import copy
from os import path
from multiprocessing import Pool
from .util import *

def toggle_bw_handle(args):
    if path.isdir(args.fname):
        toggle_bw_dir(args)
    else:
        toggle_bw_file(args)

def toggle_bw_dir(args):
    dir = args.fname
    fnames = os.listdir(dir)
    pool = Pool(args.threads)
    for f in fnames:
        args = copy.deepcopy(args)
        args.fname = path.join(dir, f)
        pool.apply_async(toggle_bw_file, [args])
    pool.close()
    pool.join()

# @safe()
def toggle_bw_file(args):
    fname = args.fname
    thres = args.thres # 50
    if not is_pic(fname):
        print('请提供图片')
        return
    print(fname)
    img = open(fname, 'rb').read()
    img = np.frombuffer(img, np.uint8)
    img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
    mean = img.mean()
    print(f'{fname} {mean}')
    if mean < thres: 
        img = 255 - img
        img = cv2.imencode(
            '.png', img, 
            [cv2.IMWRITE_PNG_COMPRESSION, 9]
        )[1]
        img =  bytes(img)
        open(fname, 'wb').write(img)
