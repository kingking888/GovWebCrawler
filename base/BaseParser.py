# @Time    : 2018/12/22 12:50 AM
# @Author  : SuanCaiYu
# @File    : BaseParser
# @Software: PyCharm

from abc import ABCMeta, abstractmethod


class BaseParser(metaclass=ABCMeta):

    @abstractmethod
    def parser_main(self, page_sources, task, logger):
        pass
