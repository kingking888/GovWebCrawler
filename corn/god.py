# @Time    : 2018/12/22 12:47 AM
# @Author  : SuanCaiYu
# @File    : god
# @Software: PyCharm
from corn.engine import Engine


class God(object):

    def __init__(self, engine: Engine):
        self.engine = engine

    def run(self):
        turn_page_flag = True
        while turn_page_flag:
            turn_page_flag = self.engine.parser_list()

        self.engine.quit()
