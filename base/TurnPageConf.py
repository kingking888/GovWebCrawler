# @Time    : 2018/12/26 14:40
# @Author  : SuanCaiYu
# @File    : TurnPageConf.py
# @Software: PyCharm


class TurnPageConf(object):

    def __init__(self, text, xpath, tag_name, page_num):
        self.text = text
        self.xpath = xpath
        self.tag_name = tag_name
        self.page_num = page_num

    def __str__(self):
        return str({'text': self.text, 'xpath': self.xpath, 'tag_name': self.tag_name, 'page_num': self.page_num})
