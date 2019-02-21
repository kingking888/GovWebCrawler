# @Time    : 2018/12/28 10:18
# @Author  : SuanCaiYu
# @File    : result_write_to_redis.py
# @Software: PyCharm
import datetime
import re
from copy import deepcopy
import time

from db_interface import database

from base.BaseResult import BaseResult
from base.Result import Result
from settings import REDIS_AUTH, REDIS_DB_INDEX, REDIS_HOST, REDIS_MSG_TASK_KEY, REDIS_PORT
from utils.redis_option import QueueFactory
from utils.tools import url_join, get_md5
from utils.db import DBOption


class WriteRedisResult(BaseResult):
    _ye = '.*[共第]\d*页.*|.*局$|.*党校$|网上调查|意见征集|在线咨询|投诉举报|区长信箱|.*设为首页.*|.*ICP备\d*号.*|.*[下上]一页.*'
    urls = QueueFactory().create(name=REDIS_MSG_TASK_KEY, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_AUTH,
                                 db=REDIS_DB_INDEX)

    def result_main(self, result: Result, task, logger, response_status, turn_page_conf):
        end_send_date = None
        if 'end_send_date' in task.keys():
            end_send_date = task.pop('end_send_date')
        for _result in result.get_result():

            if _result.get('title') and re.match(self._ye, _result.get('title')):
                continue

            row = _result.get('trigger', {})
            _type = None
            if row.get('onclick'):
                _type = 'onclick'
                _result['xpath'] = self._xpath(row.get('onclick'), '*')
            if row.get('href') and row.get('href') != '#':
                _type = 'url'
                if 'javascript' in row.get('href'):
                    _result['xpath'] = f'//*[@href="{ row.get("href") }"]'
                else:
                    _result['url'] = url_join(_result.get('base_url', ''), row.get('href'))
            if row.get('sqid'):
                _type = 'sqid'
                _result['xpath'] = f'//span[@sqid="{ row.get("sqid") }"]'
            if row.get('span_onclick'):
                _type = 'span_onclick'
                _result['xpath'] = self._xpath(row.get("span_onclick"), 'span')
            if row.get('td_onclick'):
                _type = 'td_onclick'
                _result['xpath'] = self._xpath(row.get("td_onclick"), 'td')
            if row.get('tr_onclick'):
                _type = 'tr_onclick'
                _result['xpath'] = self._xpath(row.get("tr_onclick"), 'tr')
            if row.get('a_id'):
                _type = 'a_id'
                _result['xpath'] = f'//a[@id="{ row.get("a_id") }"]'
            if not _type:
                logger.info("该行数据没有超链接或点击事件:{}".format(str(row)))
                continue
            _result['trigger'] = _type

            send_date = _result.get('send_date')
            try:
                timestamp = time.mktime(send_date.timetuple())
            except Exception as e:
                timestamp = 0
            _result['send_date'] = timestamp

            _result.update(task)
            if _result.get('url'):
                if 'update_time' in _result.keys():
                    _result.pop('update_time')
                self.urls.put(_result)
            else:
                html, img_base64 = result.browser.get_content_html(_result.get("xpath"))
                _result['html'] = html
                _result['img_base64'] = img_base64
                _result['msg_url'] = _result.pop('start_url')
                _result['url_md5'] = get_md5(str(_result.get('gov_code')) + _result.get("xpath"))
                DBOption.write_data(_result)
            _result['send_date'] = send_date
        task['end_send_date'] = end_send_date

    @classmethod
    def _xpath(cls, val, tag):
        if '"' in val:
            return f"//{tag}[@onclick='{val}']"
        else:
            return f'//{tag}[@onclick="{val}"]'
