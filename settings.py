# @Time    : 2018/12/21 11:43 PM
# @Author  : SuanCaiYu
# @File    : settings
# @Software: PyCharm


REDIS_HOST = '#'
REDIS_PORT = 9999
REDIS_AUTH = '#'
REDIS_DB_INDEX = 15
REDIS_TASK_KEY = 'environment_urls'
REDIS_MSG_TASK_KEY = 'environment_msg_urls'
REDIS_MSG_HIS_KEY = 'environment_msg_his'

# 是否加载图片
BROWSER_LOAD_IMG = False
# 是否忽略sll错误
BROWSER_IGNORE_SLL_ERROR = True
# 是否缓存到磁盘(据不可靠证实，好像没用)
BROWSER_DISK_CACHE = True
# PhantomJS 二进制文件路径
BROWSER_BIN_PATH = './bin/phantomjs.exe'
# 隐式等待时间
BROWSER_IMPLICITLY_WAIT = 30
# 页面加载超时
BROWSER_PAGELOAD_TIMEOUT = 30
# User-Agent设置
BROWSER_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36')

# 翻页后等待
TURN_PAGE_WAIT = 3
# 翻页数，不管到没到最后，翻到即停(有必要设置，PhantomJS翻页超慢)
TURN_PAGE_COUNT = 25

# 脚本名称
SCRIPT_NAME = 'GovWebFramework_LeaderMailbox'

# 日志路径
LOG_PATH = './logs/'

# 解析器列表
LIST_PARSERS = [
    'parsers.parser_list_on_keyword.ListParser',
    'parsers.parser_list_on_webpage.ListParser',
    'parsers.parser_list_on_tag_name.AllList',
    'parsers.parser_list_on_wurantousu.ListParser'
]

# 结果处理类
RESULT_CLASS = [
    # 'results.result_write_to_mongo.WriteMongoResult',
    'results.status_collect.StatusCollect',
    'results.result_write_to_redis.WriteRedisResult'
]


RESULT_DB_INFO = {
    'host': '#',
    'port': 5432,
    'user': 'postgres',
    'pwd': '#'
}
RESULT_DATABASE = 'leader_mailbox'
RESULT_TABLE = 'gov_html'
# 任务数据库
TASK_DB_INFO = {
    'host': '#',
    'port': 5432,
    'user': 'postgres',
    'pwd': '#'
}
TASK_DATABASE = 'leave_msg_spiders'
TASK_TABLE = 'leader_mailbox_tasks'

# 是否测试环境
IS_TEST = False
# 测试缓存目录
TESE_CACHE_DIR = r'D:\test_cache\cache'


RETRY_COUNT = 5
