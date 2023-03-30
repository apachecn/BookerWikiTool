import os
from os import path
from time import sleep

def pdg2pdf(args):
    from pywinauto.application import Application
    from pywinauto.keyboard import send_keys
    
    dir = args.dir
    if not path.isdir(dir):
        print('请提供目录')
        return
    fnames = os.listdir(dir)
    has_pdg = any([f.endswith('.pdg') for f in fnames])
    if not has_pdg:
        print('目录中不包含 PDG')
        return
        
    app = Application(backend='uia').start(asset('Pdg2Pic.exe'))
    # 连接软件的主窗口
    win = app.window(title_re='Pdg2Pic*', class_name_re='#32770*')
    # 设置焦点，使其处于活动状态
    win.set_focus()
    # 选择pdg目录，
    send_keys('1', 0.05, False, False,  False, True,False)
    win['TreeItem1'].click_input()
    # 设置pdg目录
    win['文件夹(F):Edit'].set_edit_text(dir)
    send_keys('{ENTER}')
    prepared_time = len(os.listdir(dirname)) / 250
    sleep(1 + prepared_time)
    send_keys('{ENTER}')
    sleep(0.5)
    send_keys('{ENTER}')
    pdf_name = path.abspath(dir) + '.pdf'
    if not path.isfile(pdf_name):
        print('转换失败')
        app.kill()
        return
    last_size = 0
    while True:
        size = path.filesize(pdf_name)
        if size == last_size: break
        last_size = size
        sleep(2)
    print(f'转换成功：{pdf_name}')
    app.kill()