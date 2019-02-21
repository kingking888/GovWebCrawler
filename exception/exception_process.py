# @Time    : 2018/12/24 18:00
# @Author  : SuanCaiYu
# @File    : exception_process.py
# @Software: PyCharm

from utils.db import DBOption
import re


class ExceptionProcess(object):
    @classmethod
    def exception(cls, task, abnormal, error):
        if 'timeout' in abnormal:
            DBOption.update_task_status(task, 'timeout')
        else:
            except1 = re.findall('\.(.*)Exception:', abnormal)
            if except1:
                DBOption.update_task_status(task, except1[0])
            else:
                DBOption.update_task_status(task, repr(error).replace("'", '"'))
