# @Time    : 2018/12/24 15:08
# @Author  : SuanCaiYu
# @File    : status_collect.py
# @Software: PyCharm
from base.BaseResult import BaseResult
from base.Result import Result
from datetime import datetime
from db_interface import database
from settings import TASK_TABLE
from utils.db import DBOption, ConnType
from utils.tools import get_md5


class StatusCollect(BaseResult):
    start_url_set = set()

    def result_main(self, result: Result, task, logger, response_status, turn_page_conf):
        dates = [x.get('send_date') for x in result.get_result()]
        max_date = self.get_max_date(dates)
        conn = DBOption.get_conn(ConnType.task_conn)
        if max_date:
            max_date = str(max_date).split(' ')[0]
            sql = f"update {TASK_TABLE} set end_send_date ='{max_date}',update_time='{datetime.now()}' where start_url='{task.get('start_url')}' and (end_send_date<'{max_date}' or (end_send_date is null))"
            DBOption.execute_task_sql(conn, sql)

        if get_md5(task.get('start_url')) in self.start_url_set:
            return

        sql = f"select * from {TASK_TABLE} where start_url='{task.get('start_url')}'"

        ret = conn.read(sql)
        next_page = str(turn_page_conf).replace("'", "''")
        if ret.data and (len(result.get_result()) > 3):
            status = str(response_status).replace("'", '"')
            sql = f"update {TASK_TABLE} set status = '{status}',update_time='{datetime.now()}',count={len(result.get_result())},parser_class='{result.parser_class}',next_page='{next_page}' where start_url='{task.get('start_url')}'"
            DBOption.execute_task_sql(conn, sql)
        else:
            data = {
                'gov_id': task.get('gov_id'),
                'gov_name': task.get('gov_name'),
                'gov_code': task.get('gov_code'),
                'start_url': task.get('start_url'),
                'update_time': datetime.now(),
                'status': str(response_status).replace("'", '"'),
                'count': len(result.get_result()),
                'next_page': next_page,
                'source': task.get('source')
            }
            if len(result.get_result()) > 3:
                data['parser_class'] = result.parser_class
            sql = database.create_insert_sql(TASK_TABLE, data)
            sql = f"{sql} ON CONFLICT (start_url) DO NOTHING"
            DBOption.execute_task_sql(conn, sql)
        self.start_url_set.add(get_md5(task.get('start_url')))

    def get_max_date(self, dates):
        max_date = None
        for date in dates:
            if not date:
                continue
            if (not max_date) or (date > max_date):
                max_date = date
        return max_date
