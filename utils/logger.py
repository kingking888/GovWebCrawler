# @Time    : 2018/12/22 12:19 AM
# @Author  : SuanCaiYu
# @File    : logger
# @Software: PyCharm

from settings import SCRIPT_NAME, LOG_PATH

import logging


def get_logger(log_name):
    log_file = f"{LOG_PATH}{SCRIPT_NAME}_{log_name}.log"
    log_format = '%(asctime)s -%(levelname)s-%(module)s-%(lineno)s: %(message)s'
    fomatter = logging.Formatter(log_format)
    logger = logging.getLogger("{}".format(SCRIPT_NAME))
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(fomatter)
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fomatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
