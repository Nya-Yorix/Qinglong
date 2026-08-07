# -*- coding: UTF-8 -*-

"""

 * @author  cyb233

 * @date  2021/1/10 10:50

"""

import sys
import time
import requests
import re
import hashlib
import os
from urllib.parse import urlparse
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# 优先从环境变量读取，若没有则从命令行参数读取
cookie = os.environ.get('HEYBOX_COOKIE')
sckey = os.environ.get('SCKEY')

# 如果环境变量没有，则尝试从命令行获取
if not cookie and len(sys.argv) >= 2:
    cookie = sys.argv[1]
if not sckey and len(sys.argv) >= 3:
    sckey = sys.argv[2]

# 必须要有 cookie，否则退出
if not cookie:
    print("错误：未提供小黑盒 Cookie。请设置环境变量 HEYBOX_COOKIE 或通过命令行第一个参数传入。")
    sys.exit(1)

sign_path = 'https://api.xiaoheihe.cn/task/sign/'
server_api = 'https://sc.ftqq.com/'

def apiRequest_get(url,cookie,params):
    params_get = params
    headers_get = {
        'Cache-Control': 'Cache-Control:public,no-cache',
        'Referer': 'http://api.maxjia.com/',
        'Accept-Encoding': 'gzip',
        'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, '
                      'like Gecko) Chrome/41.0.2272.118 Safari/537.36 ApiMaxJia/1.0',
        'Connection': 'Keep-Alive',
        'Host': 'api.xiaoheihe.cn',
        'Cookie': cookie
    }
    
    try:
        with requests.get(url, headers=headers_get, params=params_get, verify=False, timeout=300) as resp:
            res = resp.json()
            return res
    except Exception as ex:
        print(ex)


import time
import hashlib
from urllib.parse import urlparse
def gen_hkey(url: str,t:int) -> str:
    def url_to_path(url: str) -> str:
        path = urlparse(url).path
        if path and path[-1] == '/':
            path = path[:-1]
        return(path)
    def get_md5(data: str):
        md5 = hashlib.md5()
        md5.update(data.encode('utf-8'))
        result = md5.hexdigest()
        return(result)
    h = f'{url_to_path(url)}/bfhdkud_time={t}'
    h = get_md5(h)
    h = h.replace('a', 'app')
    h = h.replace('0', 'app')
    h = get_md5(h)
    h = h[:10]
    return(h)

t=time.time()
sign_time=str(int(t))
hkey=gen_hkey(sign_path,sign_time)
print('time: ',sign_time)
print('hkey: ',hkey)


def heybox(cookie):
    sign_data = apiRequest_get(sign_path + "?heybox_id=3265163&imei=8be4ead13ab97cc6&os_type=Android&os_version=5.1.1&version=1.3.118&channel=heybox_xiaomi" + "&hkey=" + hkey + "&_time=" + sign_time,cookie,"")
    if sign_data:
        if sign_data.get('status')=="ok":
            sign_result_post = '签到成功：' + str(sign_data['result']['sign_in_streak']) + '天  \n' + sign_data['msg'] + '\n'
        elif sign_data.get('status')=="login":
            sign_result_post = '签到失败，今日已签到\n'
        else:
            sign_result_post = '签到失败\n'
    else:
        sign_result_post = '签到请求失败\n'
    return sign_result_post, sign_data

if cookie:
    sign_result_post, sign_data = heybox(cookie)
    print(sign_result_post)
    try:
        if sckey:   # 如果存在 SCKEY（无论来自环境变量还是命令行）
            print("正在推送到微信")
            post_info = "?text=小黑盒每日签到&desp=" + re.sub('\\n', '  \n', sign_result_post + str(sign_data))
            post_data = requests.get(server_api + sckey + '.send' + post_info)
            print(post_data)
        else:
            print("没有SCKEY，跳过微信推送")
    except Exception as e:
        print(e)
