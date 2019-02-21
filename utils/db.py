# @Time    : 2018/12/24 18:03
# @Author  : SuanCaiYu
# @File    : db.py
# @Software: PyCharm
import time
from copy import deepcopy
from enum import Enum

from db_interface import database
from settings import TASK_DATABASE, TASK_DB_INFO, TASK_TABLE, RESULT_DB_INFO, RESULT_DATABASE, RESULT_TABLE
from datetime import datetime

from utils.tools import get_md5


class ConnType(Enum):
    task_conn = 'task_conn'
    result_conn = 'result_conn'


class DBOption(object):
    conns = {

    }

    @classmethod
    def escape_sql_like(cls, s):
        return s.replace("'", "''")

    @classmethod
    def write_data(cls, data):
        if data.get('send_date'):
            other_style_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data.get('send_date')))
        else:
            other_style_time = None
        result = {
            'gov_id': data.get('gov_id'),
            'content_md5': get_md5("".join(data.get('html'))) if isinstance(data.get('html'), list) else get_md5(
                str(data.get('html'))),
            'gov_name': data.get('gov_name'),
            'gov_code': data.get('gov_code'),
            'url': data.get('url'),
            'xpath': (cls.escape_sql_like(data.get('xpath')) if data.get('xpath') else None),
            'html': (cls.escape_sql_like(data.get('html')) if data.get('html') else None),
            'msg_url': data.get('msg_url'),
            'page_num': data.get('page_num'),
            'send_date': other_style_time,
            'title': (cls.escape_sql_like(data.get('title')) if data.get('title') else None),
            'do_time': datetime.now(),
            'url_md5': data.get('url_md5'),
            'source_type': data.get('source'),
            'img_base64': data.get('img_base64')
        }
        result_bak = deepcopy(result)
        for key in result.keys():
            if not result.get(key):
                result_bak.pop(key)
        conn = cls.get_conn(ConnType.result_conn)
        sql = database.create_insert_sql(RESULT_TABLE, result_bak)
        ret = conn.execute(sql)
        if ret.code:
            result.pop('html')
            print('ok', result)
        else:
            print(ret.result)
            if '违反唯一约束' in ret.result:
                pass
            else:
                raise Exception(ret.result)

    @classmethod
    def execute_task_sql(cls, conn, sql):
        ret = conn.execute(sql)
        print(ret.result)

    @classmethod
    def update_task_status(cls, task, status):
        sql = f"select * from {TASK_TABLE} where start_url='{task.get('start_url')}'"
        conn = cls.get_conn(ConnType.task_conn)
        ret = conn.read(sql)
        if ret.data:
            sql = f"update {TASK_TABLE} set status = '{status}',update_time='{datetime.now()}' where start_url='{task.get(' start_url')}'"
            cls.execute_task_sql(conn, sql)
        else:
            data = {
                'gov_id': task.get('gov_id'),
                'gov_name': task.get('gov_name'),
                'gov_code': task.get('gov_code'),
                'start_url': task.get('start_url'),
                'update_time': datetime.now(),
                'status': status,
                'source': task.get('source')
            }
            sql = database.create_insert_sql(TASK_TABLE, data)
            sql = f"{sql} ON CONFLICT (start_url) DO NOTHING"
            cls.execute_task_sql(conn, sql)

    @classmethod
    def create_conn(cls, db_info, db_name):
        if isinstance(db_info, dict):
            get_server = database.create_user_defined_database_server(**db_info)
        else:
            get_server = database.get_database_server_by_nick(**db_info)
        task_conn_obj = database.ConnDB(get_server, db_name)
        return task_conn_obj

    @classmethod
    def get_conn(cls, conn_type):
        conn = cls.conns.get(conn_type.value)
        db_info = TASK_DB_INFO if conn_type is ConnType.task_conn else RESULT_DB_INFO
        db_name = TASK_DATABASE if conn_type is ConnType.task_conn else RESULT_DATABASE
        if not conn:
            conn = cls.create_conn(db_info, db_name)
            cls.conns[conn_type.value] = conn
        return conn

    @classmethod
    def get_tasks(cls):
        for _ in range(5):
            conn = cls.get_conn(ConnType.task_conn)
            sql = f'select gov_id,gov_name,gov_code,start_url,parser_class,source,count,status,end_send_date from {TASK_TABLE}'
            ret = conn.read(sql)
            if ret.result > 0:
                return ret.data
            else:
                print(f'获取任务失败:{ret.result},正在重试.....')
        else:
            print(f'重试5次获取任务失败，程序退出')
            exit()
