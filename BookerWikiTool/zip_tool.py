import zipfile
from multiprocessing.pool import Pool
import os
from os import path
import re
import traceback

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
        not fname.endswith('.zip'):
        print('请提供 ZIP 文件')
        return
    print(fname)
    z = zipfile.ZipFile(fname)
    odir = re.sub(r'\.\w+$', '', fname)
    if not path.isdir(odir): os.makedirs(odir)
    if not zip_has_pw(z):
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
        
        
    