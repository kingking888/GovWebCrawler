# @Time    : 2019/1/7 14:16
# @Author  : SuanCaiYu
# @File    : redis_option.py
# @Software: PyCharm
import time
import json
import traceback
from abc import ABCMeta, abstractmethod

import redis


def catch(func):
    def decorator(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(str(e))
                time.sleep(1)

    return decorator


class QueueBase(object):
    __metaclass__ = ABCMeta

    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port

    @abstractmethod
    def put(self, value, *args, **kwargs):
        pass

    @abstractmethod
    def get(self, *args, **kwargs):
        pass

    @abstractmethod
    def size(self, *args, **kwargs):
        pass


class QueueRedis(QueueBase):
    def __init__(self, name, host='localhost', port=6379, **kwargs):
        QueueBase.__init__(self, name, host, port)
        self.__conn = redis.Redis(host=self.host, port=self.port, db=kwargs.get('db', 0),
                                  password=kwargs.get('password', None))

    @catch
    def put(self, value, *args, **kwargs):
        return self.__conn.rpush(self.name,
                                 json.dumps(value) if isinstance(value, dict) or isinstance(value, list) else value)

    @catch
    def putHead(self, value, *args, **kwargs):
        return self.__conn.lpush(self.name,
                                 json.dumps(value) if isinstance(value, dict) or isinstance(value, list) else value)

    @catch
    def get(self, *args, **kwargs):
        return self.__conn.lpop(self.name)

    @catch
    def size(self, *args, **kwargs):
        return self.__conn.llen(self.name)

    @catch
    def delete(self, *args, **kwargs):
        return self.__conn.delete(self.name)

    @catch
    def hset(self, *args, **kwargs):
        return self.__conn.hset(self.name, kwargs.get("key"), value=0)


class QueueFactory(object):
    @classmethod
    def create(cls, name, host='localhost', port=0, **kwargs):
        return QueueRedis(name, host=host, port=port, **kwargs)
