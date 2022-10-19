import win32com.client
import os, sys
from os import path

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
        except(ex): print(ex)

