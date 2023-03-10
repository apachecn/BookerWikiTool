from os import path
import os
import shutil

def flatten_dir(args):
    dir, delim = args.dir, args.delim
    if not path.isdir(dir):
        print('请提供目录！')
        return
    if dir.endswith('/') or \
        dir.endswith('\\'):
        dir = dir[:-1]
        
    for rt, _, fnames in os.walk(dir):
        rel_rt = rt[len(dir)+1:]
        for fname in fnames:
            print(path.join(rel_rt, fname))
            nfname = (
                path.join(rel_rt, fname)
                    .replace('/', delim)
                    .replace('\\', delim)
            )
            shutil.move(
                path.join(rt, fname),
                path.join(dir, nfname),
            )
            
    print('done...')
