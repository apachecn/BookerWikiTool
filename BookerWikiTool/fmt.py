import re
from os import path

def fmt_zh(text):
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z0-9_])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z0-9_])([\u4e00-\u9fff])', r'\1 \2', text)
    return text

def fmt_packt(html):
    RE_UNUSED_TAG = r'</?(article|section|span|header|link)[^>]*>'
    RE_DIV_START = r'<div[^>]*>\s*'
    RE_DIV_CONT = r'<div>([^<][\s\S]+?)</div>'
    RE_REPL_P = r'<p>\1</p>'
    RE_P_SNIPPLET = r'<p class="snipplet">(.+?)</p>'
    RE_P_SRC_CODE = r'<p class="source-code">(.+?)</p>'
    RE_REPL_PRE = r'<pre>\1</pre>'
    RE_REPL_CODE = r'<code>\1</code>'
    RE_STRONG_INLINE = r'<strong class="inline-code">(.+?)</strong>'
    RE_STRONG_CODE = r'<strong class="code">(.+?)</strong>'
    RE_PRE_NL = r'</pre>\s*<pre>'
    RE_SRC = r'src="(.+?)"'
    # 去除无用标签
    html = re.sub(RE_UNUSED_TAG, '', html)
    # DIV 内容
    html = re.sub(RE_DIV_START, '<div>', html)
    html = re.sub(RE_DIV_CONT, RE_REPL_P, html)
    # 代码段
    html = re.sub(RE_P_SRC_CODE, RE_REPL_PRE, html)
    html = re.sub(RE_P_SNIPPLET, RE_REPL_PRE, html)
    html = re.sub(RE_STRONG_INLINE, RE_REPL_CODE, html)
    html = re.sub(RE_STRONG_CODE, RE_REPL_CODE, html)
    html = re.sub(RE_PRE_NL, '\n', html)
    # 图像
    def img_src_repl(m):
        src = m.group(1)
        fname = path.basename(src)
        return f'img/{fname}'
    html = re.sub(RE_SRC, img_src_repl, html)