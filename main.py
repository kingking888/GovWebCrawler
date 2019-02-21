# @Time    : 2018/12/21 9:19 PM
# @Author  : SuanCaiYu
# @File    : main
# @Software: PyCharm
import json
import multiprocessing
import time
import traceback
from datetime import datetime

import threadpool

from corn.god import God
from corn.engine import Engine
from exception.exception_process import ExceptionProcess
from utils.db import DBOption
from utils.redis_option import QueueFactory
from settings import REDIS_TASK_KEY, REDIS_AUTH, REDIS_HOST, REDIS_PORT, REDIS_DB_INDEX, RETRY_COUNT, \
    BROWSER_PAGELOAD_TIMEOUT


def init_task():
    print('初始化任务信息')
    result = DBOption.get_tasks()
    for row in result:
        if row.get('end_send_date'):
            try:
                timestamp = time.mktime(row.get('end_send_date').timetuple())
            except:
                timestamp = 0
            row['end_send_date'] = timestamp
        rtask.put(row)


def main(run_kwargs):
    rtask = QueueFactory.create(REDIS_TASK_KEY, REDIS_HOST, REDIS_PORT, password=REDIS_AUTH, db=REDIS_DB_INDEX)
    try:
        god = God(Engine(run_kwargs))
        god.run()
    except Exception as e:
        exception_str = traceback.format_exc()
        _task = run_kwargs.get('task')
        _task['retry'] = (_task.get('retry', 0) + 1)
        _task['timeout'] = (_task.get('timeout', BROWSER_PAGELOAD_TIMEOUT) + 30)
        ExceptionProcess.exception(_task, exception_str, e)
        rtask.put(_task)
        traceback.print_exc()


def create_process(_task):
    pid = multiprocessing.Process(target=main, args=(_task,))
    pid.daemon = True
    pid.start()
    pid.join()


if __name__ == '__main__':
    rtask = QueueFactory.create(REDIS_TASK_KEY, REDIS_HOST, REDIS_PORT, password=REDIS_AUTH, db=REDIS_DB_INDEX)
    init_task()
    while True:
        if rtask.size() <= 0:
            break
        tasks = []
        task = rtask.get()
        while task:
            task = json.loads(task.decode())
            if task.get('retry', 0) > RETRY_COUNT:
                task = rtask.get()
                continue
            tasks.append(task)
            task = rtask.get()

        run_args_all = []
        log_name = datetime.strftime(datetime.now(), "%Y%m%d%H%M")
        for idx, task in enumerate(tasks):
            if task.get(
                    'start_url') == 'http://www.zjzxts.gov.cn/sun/satisfaction?page=xjgk&gkbz=1&xfxs=0600&areacode=330521':
                task['idx'] = idx
                run_args = {
                    'log_name': log_name,
                    'task': task
                }
                run_args_all.append(run_args)
        pool = threadpool.ThreadPool(7)
        reqs = threadpool.makeRequests(create_process, run_args_all)
        [pool.putRequest(req) for req in reqs]
        pool.wait()
