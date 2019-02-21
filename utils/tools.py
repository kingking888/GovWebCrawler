# @Time    : 2018/12/24 11:20
# @Author  : SuanCaiYu
# @File    : tools.py
# @Software: PyCharm
import hashlib
from urllib.parse import urljoin


def url_join(base, url):
    url = url.replace('\n', '').replace('\t', '').strip()
    if 'http' in url:
        return url
    else:
        url = url.replace('\\', '/')
        url = url.replace("\r", '').replace("\n", '').replace(" ", '')
        return urljoin(base, url)


def get_md5(val):
    m = hashlib.md5()
    try:
        m.update(val)
    except:
        m.update(val.encode('utf8'))
    return m.hexdigest()
