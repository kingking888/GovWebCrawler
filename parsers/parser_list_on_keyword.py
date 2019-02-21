# @Time    : 2018/12/24 13:39
# @Author  : SuanCaiYu
# @File    : parser_list_on_keyword.py
# @Software: PyCharm

import re
from collections import Counter
from html import unescape

from base.BaseParser import BaseParser
from base.Result import Result
from lxml import etree
from dateparser import parse


class ListParser(BaseParser):
    parser_class = 'parsers.parser_list_on_keyword.ListParser'

    def __init__(self):
        self.keywords = ['批示情况', '回复日期', '发布者', '处理状态', '写信日期', '来信日期', '已[办处受核][理结转]', '已[经]{0,1}回复', '回信日期', '邮件字号',
                         '信件标题', '信件类型', '完结', '办理单位', '^办理中', '来信标题', '已答复', '答复时间', '阅读次数', '满意度', '回复时间',
                         '\[局长信箱\]' ]
        self.row_count = 4

        self.date_regx = r'[12]?[109]?[0-9]{2}[\-年\\/.][01]?[0-9][\-月\\/.][0123]?[0-9][日]?|[01]?[0-9][\-月\\/.][0123]?[0-9][日]?'
        self.title_regx = r'.*[\u4e00-\u9fa5]+.*'

    def parser_main(self, page_sources, task, logger):
        base_url = None
        result = []
        for page_source in page_sources:
            # page_source = {'base_url':'xxxx','source':'xxxxx'}
            source = page_source.get('source')
            base_url = page_source.get('base_url')
            tag = self.find_list(source, logger)
            for _tag in tag:
                result.extend(self.parser_list(_tag))
                if result:
                    break
            if result:
                break
        if len(result) > 3:
            is_next = False
        else:
            is_next = True
        for _result in result:
            _result['base_url'] = base_url
        return Result(result, is_next)

    def find_list(self, page_source, logger):
        if not isinstance(page_source, bytes):
            page_source = page_source.encode('utf8')
        root_tag = etree.HTML(page_source)
        if not root_tag:
            root_tag = etree.HTML(page_source.decode('utf8'))
        suspect_tags = self.iter_all_tag(root_tag)
        suspect_list_tags = []
        for suspect_tag in suspect_tags:
            suspect_list_tag = self.iter_parent_tag(suspect_tag)
            if suspect_list_tag is not None:
                for _suspect_list_tag in suspect_list_tags:
                    if suspect_list_tag.get('tag') == _suspect_list_tag.get('tag'):
                        break
                else:
                    suspect_list_tags.append(suspect_list_tag)
        return suspect_list_tags

    def iter_all_tag(self, x):
        suspect_tags = []
        for i in x:
            if re.match("|".join(self.keywords), str(i.text).strip()):
                suspect_tags.append(i)
            suspect_tags.extend(self.iter_all_tag(i))
        return suspect_tags

    def iter_parent_tag(self, sub_tag):
        tag = sub_tag.getparent()
        find_result = self.jude_list(tag)
        if find_result:
            return {'tag': tag, 'row_tag': find_result[0], 'cell_tags': find_result[1]}
        elif str(tag.tag) == 'html':
            return None
        else:
            return self.iter_parent_tag(tag)

    def jude_list(self, tag):
        sub_tags = []
        sub_tag_counts = {}
        for sub_tag in tag:
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


class CellCount(object):

    @classmethod
    def all_same(cls, suspect_rows_sub_tag_names):
        last_suspect_rows_sub_tag_name = None
        for suspect_rows_sub_tag_name in suspect_rows_sub_tag_names:
            if last_suspect_rows_sub_tag_name and (last_suspect_rows_sub_tag_name != suspect_rows_sub_tag_name):
                return False
            else:
                last_suspect_rows_sub_tag_name = suspect_rows_sub_tag_name
        else:
            return True

    @classmethod
    def half_same(cls, suspect_rows_sub_tag_names):
        suspect_rows_sub_tag_name_vals = ['|'.join(x) for x in suspect_rows_sub_tag_names]
        count_vals = Counter(suspect_rows_sub_tag_name_vals)
        sorted_vals = sorted(count_vals.items(), key=lambda item: item[1], reverse=True)
        if not sorted_vals:
            return False
        key, count = sorted_vals[0]
        if count >= len(suspect_rows_sub_tag_names) / 2:
            return True
