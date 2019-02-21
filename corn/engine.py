# @Time    : 2018/12/22 12:11 AM
# @Author  : SuanCaiYu
# @File    : engine
# @Software: PyCharm
import datetime
import json
import os
import Levenshtein

from settings import SCRIPT_NAME, LIST_PARSERS, RESULT_CLASS, TURN_PAGE_COUNT
from utils.logger import get_logger
from downloader.main import Browser
from base.Result import Result
from turn_page.find_next_page_action import TurnPage


class Engine(object):

    def __init__(self, args):
        self.task = args.get('task')
        self.browser = Browser(self.task.get('timeout'))
        log_name = args.get('log_name', f"{os.getpid()}{SCRIPT_NAME}")
        self.logger = get_logger(log_name)
        self.min_date = datetime.datetime.strptime('2000-01-01', '%Y-%m-%d')
        self.logger.info(f'开始任务：{args}')
        self.__parsers = {}
        self.__results = {}
        self.page_num = 1
        self.import_all_module()
        self.turn_page_action = TurnPage()

        # 临时提取内容(用于对后续提取的内容进行判断是否相同)
        self.first_result_val = None
        self.last_result_val = None

        assert self.task, "args not find task"

        self.__start_url = self.task.get('start_url')
        assert self.__start_url, "task not find start_url"
        self.start(self.__start_url)

    def start(self, start_url):
        self.browser.load(start_url)

    def import_all_module(self):
        for parser_class in LIST_PARSERS:
            parser_obj = self.import_module(parser_class)
            self.__parsers[parser_class] = parser_obj
        for result_class in RESULT_CLASS:
            result_obj = self.import_module(result_class)
            self.__results[result_class] = result_obj

    def import_module(self, _class):
        model_path = _class.split('.')
        exec(f'from {".".join(model_path[:-1])} import {model_path[-1]}')
        parser_obj = eval(f"{model_path[-1]}()")
        return parser_obj

    @staticmethod
    def clear(val):
        """
        去除干扰词，用于对提取内容的清洗
        :param val: 清洗的文本
        :return: 清洗过后的文本
        """
        stop_word = ['的', '<', '>', '|', '[', ']', ',', '。', '，', '.', '!', '?', '！', '？']
        for word in stop_word:
            val = val.replace(word, '')
        return val

    def parser_list(self):
        result = Result([], True)
        self.browser.save_page_screenshot('./images/n.png')
        page_sources = self.get_all_html()
        response_status = self.get_response_status()
        is_all_parser = False

        if self.task.get('parser_class'):
            parser = self.__parsers.get(self.task.get('parser_class'))
            result = self._result_pipeline(parser.parser_main, page_sources=page_sources, task=self.task,
                                           logger=self.logger)
            result.parser_class = parser.parser_class
            if len(result.get_result()) < 3:
                is_all_parser = True
                self.task['count'] = 0
        else:
            is_all_parser = True
            self.task['count'] = 0

        if is_all_parser:
            for parser in self.__parsers.values():
                if not result.is_next:
                    break
                result = self._result_pipeline(parser.parser_main, page_sources=page_sources, task=self.task,
                                               logger=self.logger)
                result.parser_class = parser.parser_class
                self.task['parser_class'] = parser.parser_class
                self.task['count'] = len(result.get_result())
                self.task['status'] = str(response_status)

        # 计算提取结果相似度（采用计算莱文斯坦比） 、 (两个文本长度之和-类编辑距离)/两个文本长度之和
        val = self.clear("".join([res.get('title') for res in result.get_result()]))
        if self.first_result_val:
            first_similarity = Levenshtein.ratio(self.first_result_val, val)
            if first_similarity > 0.92:
                self.logger.info(f'当前取出的结果与第一页取出的结果相似，退出:当前第{self.page_num}页,start_url:{self.task.get("start_url")}')
                return False
        else:
            self.first_result_val = val

        if self.last_result_val:
            last_similarity = Levenshtein.ratio(self.last_result_val, val)
            if last_similarity > 0.92:
                self.logger.info(f'当前取出结果与上一页取出的结果相似，退出:当前第{self.page_num}页,start_url:{self.task.get("start_url")}')
                return False
        self.last_result_val = val

        if not val:
            self.logger.info(f'未取出结果，退出:当前第{self.page_num}页,start_url:{self.task.get("start_url")}')
            return False

        turn_page_conf = self.turn_page(page_sources)
        result.cookies = self.browser.browser.get_cookies()
        result.browser = self.browser
        for result_process in self.__results.values():
            result_process.result_main(result=result, task=self.task, logger=self.logger,
                                       response_status=response_status, turn_page_conf=turn_page_conf)

        dates = [x.get('send_date') for x in result.get_result()]
        min_date = self.get_min_date(dates)
        if min_date and datetime.datetime.now() > min_date > self.min_date and self.task.get('end_send_date'):
            if min_date < datetime.datetime.utcfromtimestamp(self.task.get('end_send_date')):
                self.logger.info(f'获取的留言日期时间已小于上次抓取的最大时间，退出,start_url:{self.task.get("start_url")}')
                return False

        if self.page_num >= TURN_PAGE_COUNT:
            self.logger.info(f'翻到指定页数，退出:当前第{self.page_num}页,start_url:{self.task.get("start_url")}')
            return False

        # 执行翻页，并判断翻页情况
        if self.__turn_page_action(turn_page_conf):
            self.logger.info(f'翻页成功，当前{self.page_num}页')
            return True
        else:
            return False

    def get_response_status(self, ):
        log_text = self.browser.get_log('har')
        if log_text == 'test':
            return 200, 'OK'
        har = json.loads(log_text[0]['message'])
        return (har['log']['entries'][0]['response']["status"], str(har['log']['entries'][0]['response']["statusText"]))

    def down_content(self):
        pass

    def get_screenshot_base64(self):
        pass

    def stop(self):
        self.quit()

    def get_all_html(self):
        return self.browser.get_all_iframe_html()

    def _result_pipeline(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, Result):
            return result
        else:
            raise TypeError('result type error , base.Result.Result()')

    def quit(self):
        self.browser.quit()

    def turn_page(self, page_sources=None):
        if not page_sources:
            page_sources = self.get_all_html()
        turn_page_conf = self.turn_page_action.find(page_sources, logger=self.logger, page_num=self.page_num)
        if not turn_page_conf:
            self.logger.info(f"{self.task.get('start_url')}:未发现可翻页特征")
            return False

        return turn_page_conf

    def __turn_page_action(self, turn_page_conf):
        flag = self.browser.turn_page(turn_page_conf, self.logger)
        if not flag:
            self.logger.info(
                f'翻页失败,当前页:{self.page_num},翻页参数:{str(turn_page_conf)},start_url:{self.task.get("start_url")}')
        else:
            self.page_num = turn_page_conf.page_num

        return flag

    def get_min_date(self, dates):
        min_date = None
        for date in dates:
            if not date:
                continue
            if (not min_date) or (date < min_date):
                min_date = date
        return min_date
