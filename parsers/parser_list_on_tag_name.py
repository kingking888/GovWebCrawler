# @Time    : 2018/11/28 10:48
# @Author  : SuanCaiYu
# @File    : parser_list_on_tag_name.py
# @Software: PyCharm
import re
from base.Result import Result
from base.BaseParser import BaseParser
from bs4 import BeautifulSoup, Tag
from dateparser import parse


class AllList(BaseParser):
    list_tags = ['td', 'tbody', 'div', 'ul', 'dl', 'li']
    list_row_tags = {'td': ['table', 'ul'], 'dl': ['dt', 'dd'], 'tbody': ['tr'],
                     'div': ['table', 'ul', 'div', 'li', 'a', 'dt'],
                     'ul': ['li'], 'li': ['a']}
    list_cell_tags = {'table': ['td'], 'tr': ['td', 'span', 'th'], 'ul': ['li', 'td', 'span', 'a'],
                      'dd': ['em', 'a', 'span'],
                      'div': ['div', 'span', 'td'],
                      'li': ['a', 'p', 'em', 'td', 'i', 'font', 'h1', 'h2', 'h3', 'h4', 'h5', 'span', 'div', 'label'],
                      'dt': ['a', 'span', 'cite'], 'a': ['li', 'span']}

    _row_count = 3
    parser_class = 'parsers.parser_list_on_tag_name.AllList'
    _table_title_keyword = r'.*来信.*|.*诉求.*|.*信件.*|.*受理.*|.*信访.*|.*[^已未]回复.*|.*标.*题.*|.*主.*题.*|.*[^正在]办理[^中完毕].*'
    _desc = r'.*投诉举报列表.*|.*社情民意反馈.*|.*热点问题回应.*|.*至.*关键字.*|.*当前位置.*'
    _page_keyword = r'.*共\d*[条页].*|.*下.?页.*|.*首页.*|.*上.?页.*'

    bad_keyword = ['登陆', '新闻中心', '政务公开', '领导之窗', 'menu', '调查征集', '政民互动', 'lbulli', '热点回应', '政策解读', '解读回应', '通知公告',
                   '政府信息公开', '办事指南', '资料下载', '民意征集', '民意调查', '领导简介', '依申请公开', '环境应急信息', '机构设置', '领导信息', '财政公开', '网上调查',
                   '咨询投诉', '意见征集', '在线访谈', '机构概况', '信息公开', '数据中心', '拍砖灌水', '污染防治', '综合督导', '规划财务', '党风廉政', '个人资料',
                   '修改资料', '在线访谈', '当前位置', '搜索', '在线申报', '相关链接', '主办', '我要写信']
    good_keyword = ['信件', '类型', '关于.*问题', '关于.*咨询', '扰民', '关于.*事宜', '您好', '你好', '来信人', '受理单位', '吗[?？]', '怎么办[?？]', '焚烧',
                    '工厂', '小区', '房', '什么']

    def __init__(self):
        for filename in ['sensitive_word_userdict.txt', 'stb_sensitive_word_userdict.txt']:
            with open(f'./data/{filename}', 'r', encoding='utf8') as fp:
                line = fp.readline()
                while line:
                    if line:
                        words = line.split()
                        if words:
                            self.good_keyword.append(words[0].strip().replace('\ufeff', ''))
                    line = fp.readline()
        self.keywords = ['回复日期', '发布者', '处理状态', '写信日期', '来信日期', '已[办处核][理结转]', '已[经]{0,1}回复', '回信日期', '邮件字号',
                         '信件标题', '信件类型', '完结', '办理单位']
        self.row_count = 4

        self.date_regx = r'[12]?[109]?[0-9]{2}[\-年\\/.][01]?[0-9][\-月\\/.][0123]?[0-9][日]?|[01]?[0-9][\-月\\/.][0123]?[0-9][日]?'
        self.title_regx = r'.*[\u4e00-\u9fa5]+.*'

    def parser_main(self, page_sources, task, logger):
        result = []
        for page_source in page_sources:
            base_url = page_source.get('base_url')
            source = page_source.get('source')
            _list = self.get_list(source)
            _list = self.add_score(_list)
            _result = self.get_all_list(_list)
            for result_item in _result:
                result_item['base_url'] = base_url
            result.extend(_result)
        if len(result) >= 3:
            is_next = False
        else:
            is_next = True
        return Result(result, is_next)

        pass

    def find_child_tags(self, parent_node, tag_name):
        _tags = []
        _tag = parent_node.find(tag_name)
        if _tag:
            _tags.append(_tag)
            _tags.extend(_tag.find_next_siblings(tag_name))
        return _tags

    def get_list(self, page_source):
        suspect_tags = []
        soup = BeautifulSoup(page_source, 'lxml')
        tags = []
        for list_tag in self.list_tags:
            _tags = soup.find_all(list_tag)
            tags.extend([{"list_tag": list_tag, 'element': x} for x in _tags])

        for tag in tags:
            list_element = tag.get('element')
            for list_row_tag in self.list_row_tags.get(tag.get('list_tag')):
                _row_tags = self.find_child_tags(list_element, list_row_tag)
                if len(_row_tags) > self._row_count:
                    suspect_tags.append(
                        {'list_tag': tag.get('list_tag'), 'row_tag': list_row_tag, 'element': list_element})
                    break

        return suspect_tags

    def add_score(self, sus_list):
        x = []
        for sus in sus_list:
            html = sus.get('element').prettify()
            c = {'tag': sus}
            if re.match('.*网?站?首.{0,5}页.*', html, re.S):
                score = c.get('score', 0)
                c['score'] = score - 1
            for word in self.good_keyword:
                if re.match(f'.*{word}.*', html, re.S):
                    score = c.get('score', 0)
                    c['score'] = score + 1
            for word in self.bad_keyword:
                if re.match(f'.*{word}.*', html, re.S):
                    score = c.get('score', 0)
                    c['score'] = score - 2
            dates = re.findall(self.date_regx, html, re.S)
            score = c.get('score', 0)
            c['score'] = score + len(dates)
            x.append(c)
        x = sorted(x, key=lambda v: v.get('score', 0), reverse=True)

        min_list_len = None
        max_score = 0
        use_tag = None
        for _x in x:
            if max_score == 0:
                max_score = _x.get('score', 0)
            elif _x.get('score', 0) < max_score:
                break
            if min_list_len and len(_x.get('tag', {}).get('element').prettify()) < min_list_len:
                use_tag = _x.get('tag')
            else:
                min_list_len = len(_x.get('tag', {}).get('element').prettify())
        if use_tag:
            return [use_tag]
        else:
            return []
        # result = []
        # for _x in x:
        #     if _x.get('score', 0) > 0:
        #         result.append(_x.get('tag'))
        #     else:
        #         if (not result) and x:
        #             result.append(x[0].get('tag'))
        # return result

    def get_all_list(self, tags):
        result = []
        for _tag in tags:
            row_tag_name = _tag.get('row_tag')
            list_element = _tag.get('element')
            rows = self.find_child_tags(list_element, row_tag_name)
            result.extend(self.process_rows(rows, row_tag_name))
        return result

    def process_rows(self, rows, row_tag_name):
        result = []
        for idx, row in enumerate(rows):

            # 判断特殊行
            if idx in [0]:
                if re.match(self._desc, row.prettify(), re.S):
                    continue
            # 判断标题行
            if idx in [0, 1, 3, 2]:
                if re.match(self._table_title_keyword, row.prettify(), re.S):
                    continue
            # 判断是否翻页行
            if re.match(self._page_keyword, row.prettify(), re.S):
                continue

            trigger = self.get_url(row)
            dates = []
            titles = []
            texts = self.parser_row_all_text(row, self.list_cell_tags.get(row_tag_name))
            for text in texts:
                _dates = re.match(self.date_regx, text)
                _titles = re.findall(self.title_regx, text)
                if _dates:
                    dates.append(text)
                elif _titles and (not re.match('|'.join(self.keywords), text)):
                    titles.extend(_titles)
            result.append({'trigger': trigger, 'send_date': self.get_min_date(dates), 'title': '|'.join(titles)})
        return result

    def parser_row_all_text(self, row, cell_tag_names):
        result = []
        for sub_tag in row.contents:
            if not isinstance(sub_tag, Tag):
                continue
            if re.match('|'.join(cell_tag_names), str(sub_tag.name)):
                result.append(self.get_html_text(sub_tag.prettify()))
            else:
                result.extend(self.parser_row_all_text(sub_tag, cell_tag_names))
        return result

    def get_html_text(self, html, replcae_space=True):
        dr = re.compile(r'<[^>]+>', re.S)
        dr_replace_script = re.compile(r'<script.*?</script>', re.S)
        dd = dr_replace_script.sub('', html)
        dd = dr.sub('', dd)
        if replcae_space:
            dd = dd.replace(' ', '')
        return dd.replace('\n', '')

    def get_url(self, tag):
        all_a = tag.find_all('a')
        url_result = {}
        for a in all_a:
            href = a.attrs.get('href')
            onclick = a.attrs.get('onclick')
            a_id = a.attrs.get('id')
            if href and re.match(
                    r'complaints\.php|.*list\.aspx\?bm=.*|questions\.php|suggestions\.php|.*page610\?article_category=222.*|.*index\.action\?unit=.*',
                    href):
                continue
            if href or onclick or a_id:
                _bool = href != 'javascript:void(0);' and href != 'javascript:;' and href != 'javascript:void(0)' and href != './' and href != 'javascript:void()'
                if href and _bool and href != '#' and not url_result.get('href'):
                    url_result['href'] = href
                url_result['onclick'] = onclick
                url_result['a_id'] = a_id
                url_result['element'] = a
        if (not url_result.get('href')) and (not url_result.get('onclick')) and (not url_result.get('a_id')):
            all_span = tag.find_all('span')
            for span in all_span:
                _class = span.attrs.get('class')
                sqid = span.attrs.get('sqid')
                _onclick = span.attrs.get('onclick')
                if _class and 'pageSkipCls' in _class:
                    url_result['sqid'] = sqid
                    url_result['element'] = span
                if _onclick:
                    url_result['span_onclick'] = _onclick
                    url_result['element'] = span

            if (not url_result.get('sqid')) and (not url_result.get('span_onclick')):
                all_td = tag.find_all('td')
                for td in all_td:
                    onclick = td.attrs.get('onclick')
                    if onclick:
                        url_result['td_onclick'] = onclick
                        url_result['element'] = td

                if not url_result.get('td_onclick'):
                    onclick = tag.attrs.get('onclick')
                    if onclick:
                        url_result['tr_onclick'] = onclick
                        url_result['element'] = tag
                if (not url_result.get('td_onclick')) and (not url_result.get('tr_onclick')):
                    href1 = tag.attrs.get('href')
                    if href1:
                        url_result['href'] = href1
                        url_result['element'] = tag
        return url_result

    def get_min_date(self, dates):
        min_date = None
        for date in dates:
            _date = parse(date)
            if not _date:
                continue
            if (not min_date) or (_date < min_date):
                min_date = _date
        return min_date
