# @Time    : 2018/12/24 11:35
# @Author  : SuanCaiYu
# @File    : BaseResult.py
# @Software: PyCharm
from abc import ABCMeta, abstractmethod
from base.Result import Result


class BaseResult(metaclass=ABCMeta):

    @abstractmethod
    def result_main(self, result: Result, task, logger, response_status, turn_page_conf):
        pass
