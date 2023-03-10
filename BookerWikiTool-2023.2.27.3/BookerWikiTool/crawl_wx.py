import pandas as pd
from os import path
import re
import subprocess as subp
import json

POST_TIME = '发布时间'
ART_LINK = '文章链接'
DIR = path.dirname(path.abspath(__file__))

config_tmpl = {
    "name": "{name}",
    "url": "http://mp.weixin.qq.com",
    "link": ".summary .link, .summary li a",
    "title": "#activity-name",
    "content": "#js_content",
    "remove": "",
    "optiMode": "thres",
	"external": path.join(DIR, 'wx_external.py'),
	"retry": 3,
	"list":[],
}

def crawl_wx(args):
    fname = args.fname
    size = args.size
    if not fname.endswith('.xls') and \
        not fname.endswith('.xlsx'):
        print('请提供 EXCEL 文件')
        return
    gzh_name = re.sub(r'\.\w+$', '', path.basename(fname))
    df = pd.read_excel(fname)
    if not POST_TIME in df.columns or \
        not ART_LINK in df.columns:
        print(f'未找到【{POST_TIME}】和【{ART_LINK}】')
        return
    df = df[df[ART_LINK].str.startswith('http')]
    df.sort_values(by=POST_TIME, inplace=True, ascending=False)
    for i in range(0, len(df), size):
        df_part = df.iloc[i:i+size]
        st = df_part[POST_TIME].iloc[-1].replace('-', '')[:6]
        ed = df_part[POST_TIME].iloc[0].replace('-', '')[:6]
        name = f'{gzh_name} {st}-{ed}'
        config = config_tmpl.copy()
        config['name'] = name
        config['list'] = df_part[ART_LINK].tolist()
        config['optiMode'] = args.opti_mode
        config_fname = f'config_{gzh_name}_{st}_{ed}.json'
        open(config_fname, 'w', encoding='utf8').write(json.dumps(config))
        subp.Popen(['crawl-epub', config_fname], shell=True).communicate()