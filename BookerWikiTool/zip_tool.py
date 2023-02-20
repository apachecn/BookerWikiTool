import zipfile
import rarfile
from multiprocessing.pool import Pool
import os
from os import path
import re
import traceback
from .util import *

def zip_has_pw(z):
    return any([
        info.flag_bits & 0x1 
        for info in z.infolist()
    ])
        
        
def crack_single(z, dir, pw):
    try:
        z.extractall(dir, pwd=pw.encode('utf8'))
        print(f'{pw} 破解成功，已解压到 {dir}')
        return True
    except: 
        print(f'{pw} 破解失败')
        return False

def crack_zip(args):
    fname = args.fname
    pw_fname = args.pw
    if not path.isfile(fname) or \
        (not fname.endswith('.zip') and \
         not fname.endswith('.rar')):
        print('请提供 ZIP 或 RAR 文件')
        return
    print(fname)
    if fname.endswith('.zip'):
        z = zipfile.ZipFile(fname)
    else:
        z = rarfile.RarFile(fname)
    odir = re.sub(r'\.\w+$', '', fname)
    if not path.isdir(odir): os.makedirs(odir)
    has_pw = (
        zip_has_pw(z) 
        if fname.endswith('.zip') 
        else z.needs_password()
    )
    if not has_pw:
        z.extractall(odir)
        print(f'{fname} 未加密，已解压到 {odir}')
        z.close()
        return
    pw_list = open(pw_fname, encoding='utf8').read().split('\n')
    pw_list = list(filter(None, [pw.strip() for pw in pw_list]))
    print(f'载入密码{len(pw_list)}个')
    # pool = Pool(args.threads)
    # res = []
    for pw in pw_list:
        # pool.apply_async(tr_crack_zip, [z, odir, pw, res])
        res = crack_single(z, odir, pw)
        if res: break
    # pool.close()
    # pool.join()
    z.close()
        
        
    