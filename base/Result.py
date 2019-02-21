# @Time    : 2018/12/22 12:59 AM
# @Author  : SuanCaiYu
# @File    : Result
# @Software: PyCharm
import re


class Result(object):
    _page_keyword = r'.*共\d*[条页].*|.*下.?页.*|.*首页.*|.*上.?页.*'

    def __init__(self, result: list, is_next: bool):
        self.__result = result
        self.is_next = is_next
        self.parser_class = None
        self.__is_clear = False
        self.cookies = None
        self.browser = None
        print(result)

    def get_result(self):
        if not self.__is_clear:
            tags = []
            result_len = len(self.__result)
            for _ in range(result_len):
                result = self.__result.pop(0)
                if (result.get('trigger', {}).get('href', '') not in tags) and (
                        result.get('title', "").strip() != ""):
                    self.__result.append(result)
                    tags.append(result.get('trigger', {}).get('href', ''))
                elif not result.get('trigger', {}).get('href'):
                    self.__result.append(result)
            self.__is_clear = True
        return self.__result
