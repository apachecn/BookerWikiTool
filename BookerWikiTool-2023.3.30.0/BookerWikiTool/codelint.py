import re
from .util import *

RE_SL_COMM = r'//.*?$'
RE_ML_COMM = r'/\*[\s\S]*?\*/'
RE_SL_STR = r'".*?(?<!\\)(\\\\)*"'
RE_SL_STR2 = r"'.*?(?<!\\)(\\\\)*'"
RE_ML_STR = r'"""[\s\S]*?"""'
RE_ML_STR2 = r"'''[\s\S]*?'''"
RE_RAW_STR = r'`[\s\S]*?`'
RE_FOR = r'for\s*\([^\)]+\)'

re_arr = [
    RE_SL_COMM, RE_ML_COMM, 
    RE_SL_STR, RE_SL_STR2,
    RE_ML_STR, RE_ML_STR2, 
    RE_RAW_STR, RE_FOR
]

def code_lint(s):
    s = s.replace('\r', '')
    # 替换注释和字符串
    tokens = []
    def repl_func(m):
        s = m.group()
        tokens.append(s)
        ph = f'$TKN{len(tokens)-1}$'
        return ph
    for r in re_arr:
        s = re.sub(r, repl_func, s, flags=re.M)
    # 检查每一行
    ind = 0
    lines = s.split('\n')
    for i in range(len(lines)):
        l = lines[i].strip()
        ii = l.find('{')
        # xxx{yyy
        if ii != -1 and ii != len(l) - 1:
            nxline = l[ii+1:].strip()
            lines.insert(i + 1, nxline)
            l = l[:ii+1].strip()
        # xxx}yyy
        ii = l.find('}')
        if ii != -1 and ii != 0:
            nxline = l[ii:].strip()
            lines.insert(i + 1, nxline)
            l = l[:ii].strip()
        # xxx;yyy
        ii = l.find(';')
        if ii != -1 and ii != len(l) - 1:
            nxline = l[ii+1:].strip()
            lines.insert(i + 1, nxline)
            l = l[:ii+1].strip()
        if l.startswith('}'):
            ind = max(0, ind - 4)
        lines[i] = ' ' * ind + l
        if l.endswith('{'):
            ind += 4
            
    # 去除独占一行的分号
    lines = [l for l in lines if l.strip() != ';']
    # 上移独占一行的左花括号
    for i in range(len(lines) - 1, 0, -1):
        l = lines[i]
        if l.strip() == '{':
            del lines[i]
            lines[i - 1] += ' {'
    # 还原注释和字符串
    s = '\n'.join(lines)
    for i, tk in enumerate(tokens):
        s = s.replace(f'$TKN{i}$', tk)
    return s
    
def code_lint_file(args):
    fname = args.fname
    if not is_c_style_code(fname):
        print('请提供 C 风格代码！')
        return
    print(fname)
    cont = open(fname, encoding='utf8').read()
    cont = code_lint(cont)
    print(cont)
    open(fname, 'w', encoding='utf8').write(cont)
