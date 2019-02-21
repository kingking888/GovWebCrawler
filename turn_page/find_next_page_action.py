# @Time    : 2018/12/25 16:12
# @Author  : SuanCaiYu
# @File    : find_next_page_action.py
# @Software: PyCharm
import re

from bs4 import BeautifulSoup
from base.TurnPageConf import TurnPageConf


class TurnPage(object):
    _next_keywords = r'.{0,1}下页.{0,1}|.{0,1}下一页.{0,1}|.{0,1}后页.{0,1}|.{0,1}后一页.{0,1}|»|›|>$'
    page_keywords = ''
    next_tag_names = ['li', 'label', 'div', 'input', 'img', 'span', 'td']

    def find(self, page_sources, logger, page_num):
        page_num = page_num + 1
        self.page_keywords = u'^%s$|^0%s$|^\[%s\]$|^%s[\s]*$' % (
            str(page_num), str(page_num), str(page_num), str(page_num))
        for page_source in page_sources:
            source = page_source.get('source')
            find_text, xpath = self.find_next_on_a_tag(source, page_num)
            if find_text or xpath:
                return TurnPageConf(find_text, xpath, 'a', page_num)

        for next_tag_name in self.next_tag_names:
            for page_source in page_sources:
                source = page_source.get('source')
                find_text, xpath = self.find_next_on_other_tag(source, next_tag_name)
                if find_text or xpath:
                    return TurnPageConf(find_text, xpath, next_tag_name, page_num)

        return None

    def find_next_on_a_tag(self, source, page_num):
        soup = BeautifulSoup(source, 'lxml')
        a_tags = soup.find_all('a')
        for a_tag in a_tags:
            text = a_tag.get_text()
            find_text = a_tag.text
            attrs = str(a_tag.prettify())
            url = a_tag.attrs.get('href', None)
            _url = '#'
            if url and 'javascript' in url:
                _url = url
                url = '#'
            if url and url != '#':
                if '"' in url:
                    tag_xpath = "//a[@href='%s']" % url
                else:
                    tag_xpath = '//a[@href="%s"]' % url
            else:
                url = a_tag.attrs.get('onclick')
                if url:
                    if '"' in url:
                        tag_xpath = "//a[@onclick='%s']" % url
                    else:
                        tag_xpath = '//a[@onclick="%s"]' % url

                elif _url != 'javascript:' and _url != 'javascript:;' and _url != 'javascript:void(0);' and _url != 'javascript:void(0)' and _url != '#':
                    url = _url
                    if '"' in url:
                        tag_xpath = "//a[@href='%s']" % url
                    else:
                        tag_xpath = '//a[@href="%s"]' % url
                else:
                    url = a_tag.attrs.get('data-page')
                    url1 = a_tag.attrs.get('icon')
                    url2 = a_tag.attrs.get('paged')
                    id1 = a_tag.attrs.get('id')
                    dpi = a_tag.attrs.get('data-page-index')
                    if url:
                        tag_xpath = '//a[@data-page="%s"]' % url
                    elif url1:
                        tag_xpath = '//a[@icon="%s"]' % url1
                    elif url2:
                        tag_xpath = '//a[@paged="%s"]' % url2
                    elif id1:
                        tag_xpath = '//a[@id="%s"]' % id1
                    elif dpi:
                        tag_xpath = '//a[@data-page-index="%s"]' % dpi
                    elif text == '':
                        continue
                    else:
                        tag_xpath = None

            if text and re.match(self._next_keywords, text.replace("\n", "").replace("\t", '').replace(" ", '')):
                if ("nivo-control" in attrs) or ('/cms/cms/html/npsypqrmzf/' in attrs):
                    continue
                if tag_xpath and tag_xpath != '':
                    return find_text, tag_xpath
            elif text and re.match(self.page_keywords, text.replace("\n", "").replace("\t", '').replace(" ", '')):
                if ("nivo-control" in attrs) or ('/cms/cms/html/npsyp qrmzf/' in attrs):
                    continue
                if tag_xpath and tag_xpath != '':
                    return find_text, tag_xpath

            kw = f"^.{0,3}第{ page_num }页.{0,3}|.*下一页.*|.*后页.*|.*下.*页.*|.*pagination-next.*|.*MovePage\(1.*|.*NextPage.*|^.{0,3}后一页.{0,3}|.*ui-paginator-next.*|.*[Nn]{1}ext[01]{0,2}\.gif.*|.*but_next01\.gif.*|.*arrow-right02\.gif.*|.*gonext\.gif.*|.*images/24\.gif.*|.*lineforward\.gif.*|.*nextn\.gif.*"
            if re.match(kw, attrs, re.S):
                if tag_xpath and tag_xpath != '':
                    return find_text, tag_xpath
        return None, None

    def find_next_on_other_tag(self, source, tag_name):
        page_keywords = self.page_keywords
        except_attrs = ['onclick', 'id', 'name', 'class']
        soup = BeautifulSoup(source, 'lxml')
        td_tags = soup.find_all(tag_name)
        _text, _xpath = None, None
        for td in td_tags:
            xpath = '//' + tag_name + '[{}]'
            xpath_list = []
            for attr in except_attrs:
                if td.attrs.get(attr, '') != '':
                    _attr = td.attrs.get(attr, '')
                    if attr == 'class':
                        _attr = ' '.join(_attr)
                    xpath_list.append('@{}="{}"'.format(attr, _attr))
            xpath = xpath.format(' and '.join(xpath_list))
            if xpath == '//' + tag_name + '[]':
                xpath = '//{}'.format(tag_name)

            text = td.get_text()

            if text and re.match(self._next_keywords, text):
                if (not _xpath) or (len(xpath) > len(_xpath)):
                    _text, _xpath = text, xpath
            elif text and re.match(page_keywords, text):
                if (not _xpath) or (len(xpath) > len(_xpath)):
                    _text, _xpath = text, xpath
            attrs = str(td.attrs)
            kw = ".*下一页.*|.*后页.*|.*下页.*|.*pagination-next.*|.*MovePage\(1.*|.*NextPage.*|.*nextPage.*|.*后一页.*|.*pager-next.*|.*>.*"
            if re.match(kw, attrs, re.S):
                if not _xpath:
                    _text, _xpath = text, xpath
        return _text, _xpath
