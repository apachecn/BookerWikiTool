import zipfile
from multiprocessing.pool import Pool
import os
from os import path

def zip_has_pw(z):
    return any([
        info.flag_bits & 0x1 
        for info in z.infolist()
    ])
        
        
def crack_zip(z, dir, pw, res):
    if res: return
    try:
        z.extractall(dir, password=pw.encode('utf8'))
        res.append(pw)
    except: pass

def crack_zip(args):
    fname = args.fname
    pw_fname = args.pw
    if not path.isfile(fname) or
        not fname.endswith('.zip'):
        print('请提供 ZIP 文件')
        return
    z = zipfile.ZipFile(fname)
    odir = re.sub(r'\.\w+$', '', fname)
    if not path.isdir(odir): os.makedirs(odir)
    if not zip_has_pw(z):
        print(f'{fname} 未加密')
        z.extractall(odir)
        z.close()
        return
    pw_list = open(pw_fname, encoding='utf8').read().split('\n')
    pw_list = filter(None, [pw.strip() for pw in pw_list])
    pool = Pool(args.threads)
    res = []
    for pw in pw_list:
        pool.apply_async(crack_zip, args=[z, odir, pw, res])
    pool.close()
    pool.join()
    if res:
        print(f'{fname} 破解成功，密码：{res[0]}')
    else:
        print(f'{fname} 破解失败')
        
        
    