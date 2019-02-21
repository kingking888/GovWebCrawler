# @Time    : 2018/12/24 13:43
# @Author  : SuanCaiYu
# @File    : parser_list_on_webpage.py
# @Software: PyCharm
import re

from dateparser import parse
from lxml.etree import _Comment

from base.BaseParser import BaseParser
from base.Result import Result
from parsers.parser_list_on_keyword import CellCount
from lxml import etree
from html import unescape


class ListParser(BaseParser):
    row_count = 3

    bad_keyword = ['登陆', '新闻中心', '政务公开', '领导之窗', 'menu', '调查征集', '政民互动', 'lbulli', '热点回应', '政策解读', '解读回应', '通知公告',
                   '政府信息公开', '办事指南', '资料下载', '民意征集', '民意调查', '领导简介', '依申请公开', '环境应急信息', '机构设置', '领导信息', '财政公开', '网上调查',
                   '咨询投诉', '意见征集', '在线访谈', '机构概况', '信息公开', '数据中心', '拍砖灌水', '污染防治', '综合督导', '规划财务', '党风廉政', '个人资料',
                   '修改资料']
    good_keyword = ['信件', '类型', '关于.*问题', '关于.*咨询', '扰民', '关于.*事宜', '您好', '你好', '来信人', '受理单位', '吗[?？]', '怎么办[?？]']

    parser_class = 'parsers.parser_list_on_webpage.ListParser'

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
        sus_list = []
        for page_source in page_sources:
            source = page_source.get('source')
            for _tag in self.find_list(source):
                _tag['base_url'] = page_source.get('base_url')
                sus_list.append(_tag)
        tag = self.add_score(sus_list)
        if not tag:
            return Result([], True)
        base_url = tag.get('base_url')
        result = self.parser_list(tag)
        for _result in result:
            _result['base_url'] = base_url
        if len(result) > 3:
            is_next = False
        else:
            is_next = True
        return Result(result, is_next)

    def find_list(self, source):
        root_tag = etree.HTML(source)
        return self.iter_all_tag_find_list(root_tag)

    def iter_all_tag_find_list(self, root):
        msg_list = []
        vals = self.jude_list(root)
        if vals:
            msg_list.append({'tag': root, 'row_tag': vals[0], 'cell_tags': vals[1]})
        else:
            for sub_tag in root:
                msg_list.extend(self.iter_all_tag_find_list(sub_tag))
        return msg_list

    def add_score(self, sus_list):
        x = []
        for sus in sus_list:
            html = etree.tostring(sus.get('tag'))
            html = unescape(html.decode('utf8'))
            c = {'tag': sus}
            if re.match('.*网?站?首.{0,5}页.*', html, re.S):
                score = c.get('score', 0)
                c['score'] = score - 1
            for word in self.good_keyword:
                if re.match(f'.*{word}.*', html, re.S):
                    score = c.get('score', 0)
                    c['score'] = score + 1
            datas = re.findall(self.date_regx, html, re.S)
            score = c.get('score', 0)
            c['score'] = score + len(datas)
            for word in self.bad_keyword:
                if re.match(f'.*{word}.*', html, re.S):
                    score = c.get('score', 0)
                    c['score'] = score - 1
            x.append(c)
        x = sorted(x, key=lambda v: v.get('score', 0), reverse=True)
        if x:
            if x[0].get('score', 0) < 0:
                return None
            return x[0].get('tag')
        return None

    def jude_list(self, tag):
        sub_tags = []
        sub_tag_counts = {}
        for sub_tag in tag:
            if isinstance(sub_tag, _Comment):
                continue
            sub_tags.append(sub_tag)
            tmp_count = sub_tag_counts.get(sub_tag.tag, 0)
            sub_tag_counts[sub_tag.tag] = tmp_count + 1
        max_count = 0
        if sub_tag_counts.values():
            max_count = sorted(sub_tag_counts.values(), reverse=True)[0]

        if max_count < self.row_count:
            return False

        suspect_row_tag_text = None
        for tmp_tag_count in sub_tag_counts.items():
            if tmp_tag_count[1] == max_count:
                suspect_row_tag_text = tmp_tag_count[0]
                break

        suspect_rows = []
        for sub_tag in sub_tags:
            if str(sub_tag.tag) == suspect_row_tag_text:
                suspect_rows.append(sub_tag)

        suspect_rows_sub_tag_names = []
        for suspect_row in suspect_rows:
            suspect_row_sub_tag_name = []
            for suspect_row_sub_tag in suspect_row:
                if isinstance(suspect_row_sub_tag, _Comment):
                    continue
                suspect_row_sub_tag_name.append(str(suspect_row_sub_tag.tag))
            if suspect_row_sub_tag_name and (len(suspect_row_sub_tag_name) > 1):
                suspect_rows_sub_tag_names.append(suspect_row_sub_tag_name)
        if len(suspect_rows_sub_tag_names) < self.row_count:
            return False

        result = CellCount.half_same(suspect_rows_sub_tag_names)
        if result:
            if suspect_rows_sub_tag_names:
                cell_tags = []
                for _cell in suspect_rows_sub_tag_names:
                    cell_tags.extend(_cell)
                cell_tags = list(set(cell_tags))
                return suspect_row_tag_text, cell_tags
            else:
                return False
        else:
            return False

    def parser_list(self, content_list):
        content_tag = content_list['tag']
        row_tags = []

        for sub_tag in content_tag:
            if isinstance(sub_tag, str):
                print(sub_tag, '是一个文本')
                continue
            if sub_tag.tag == content_list.get('row_tag'):
                row_tags.append(sub_tag)

        result = []
        for row_tag in row_tags:
            trigger = self.parser_url(row_tag)
            texts = self.parser_row_text(row_tag, content_list.get('cell_tags'))
            dates = []
            titles = []
            for text in texts:
                _dates = re.match(self.date_regx, text)
                _titles = re.findall(self.title_regx, text)
                if _dates:
                    dates.append(text)
                elif _titles and (not re.match('|'.join(self.keywords), text)):
                    titles.extend(_titles)
            result.append({'trigger': trigger, 'send_date': self.get_min_date(dates), 'title': '|'.join(titles)})
        return result

    def parser_url(self, row_tag):
        url_result = {}
        all_a = self.find_sub_tags(row_tag, 'a')
        for a_tag in all_a:
            href = a_tag.attrib.get('href')
            onclick = a_tag.attrib.get('onclick')
            a_id = a_tag.attrib.get('id')
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
                url_result['element'] = a_tag

        if (not url_result.get('href')) and (not url_result.get('onclick')) and (not url_result.get('a_id')):
            all_span = self.find_sub_tags(row_tag, 'span')
            for span in all_span:
                _class = span.attrib.get('class')
                sqid = span.attrib.get('sqid')
                _onclick = span.attrib.get('onclick')
                if _class and 'pageSkipCls' in _class:
                    url_result['sqid'] = sqid
                    url_result['element'] = span
                if _onclick:
                    url_result['span_onclick'] = _onclick
                    url_result['element'] = span

            if (not url_result.get('sqid')) and (not url_result.get('span_onclick')):
                all_td = self.find_sub_tags(row_tag, 'td')
                for td in all_td:
                    onclick = td.attrib.get('onclick')
                    if onclick:
                        url_result['td_onclick'] = onclick
                        url_result['element'] = td

                if not url_result.get('td_onclick'):
                    onclick = row_tag.attrib.get('onclick')
                    if onclick:
                        url_result['tr_onclick'] = onclick
                        url_result['element'] = row_tag
                if (not url_result.get('td_onclick')) and (not url_result.get('tr_onclick')):
                    href1 = row_tag.attrib.get('href')
                    if href1:
                        url_result['href'] = href1
                        url_result['element'] = row_tag
        return url_result

    def find_sub_tags(self, parent_tag, find_tag_name):
        sub_tags = []
        for sub_tag in parent_tag:
            if str(sub_tag.tag) == find_tag_name:
                sub_tags.append(sub_tag)
            else:
                sub_tags.extend(self.find_sub_tags(sub_tag, find_tag_name))
        return sub_tags

    def parser_row_text(self, row_tag, cell_tag_names):
        contents = []
        for sub_tag in row_tag:
            if re.match('|'.join(cell_tag_names), str(sub_tag.tag)):
                contents.append(self.get_html_text(etree.tostring(sub_tag)))
        return contents

        pass

    def get_html_text(self, html, replcae_space=True):
        if isinstance(html, bytes):
            html = html.decode('utf8')
        dr = re.compile(r'<[^>]+>', re.S)
        dr_replace_script = re.compile(r'<script.*?</script>', re.S)
        dd = dr_replace_script.sub('', html)
        dd = dr.sub('', dd)
        if replcae_space:
            dd = dd.replace(' ', '')
        return unescape(dd.replace('\n', ''))

    def get_min_date(self, dates):
        min_date = None
        for date in dates:
            _date = parse(date)
            if not _date:
                continue
            if (not min_date) or (_date < min_date):
                min_date = _date
        return min_date
