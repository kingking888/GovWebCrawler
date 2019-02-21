# @Time    : 2018/12/24 13:41
# @Author  : SuanCaiYu
# @File    : result_write_to_mongo.py
# @Software: PyCharm
from pymongo import MongoClient

from base.BaseResult import BaseResult


class WriteMongoResult(BaseResult):

    def __init__(self):
        mongoCnn = MongoClient(host='127.0.0.1', port=27017)
        db = mongoCnn['govs']
        self.col = db['gov_html_2018_12_27']

    def result_main(self, result, task, logger, response_status, turn_page_conf):
        results = result.get_result()
        print(f'结果长度:{len(results)}')
        for _result in results:
            _result.update(task)
        if results:
            self.col.insert(results)
