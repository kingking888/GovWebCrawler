# @Time    : 2019/1/9 9:52
# @Author  : SuanCaiYu
# @File    : parser_list_on_wurantousu.py
# @Software: PyCharm

from lxml import etree

from base.BaseParser import BaseParser
from base.Result import Result

from dateparser import parse


class ListParser(BaseParser):
    parser_class = 'parsers.parser_list_on_wurantousu.ListParser'

    def parser_main(self, page_sources, task, logger):
        results = []
        for page_source in page_sources:
            source = page_source.get('source')
            if isinstance(source, bytes):
                source = source.decode()
            select = etree.HTML(source)
            items = select.xpath('//div[@class="is is1"]/div[@class="cont"]/div[@class="item"]')
            for item in items:
                title = item.xpath('div[@class="c"]/h5/a/@title')
                href = item.xpath('div[@class="c"]/h5/a/@href')
                send_date = item.xpath('div[@class="c"]/div[@class="ctrl"]/span[@class="time"]/text()')
                if title:
                    title = title[0]
                else:
                    title = ''
                if href:
                    href = href[0]
                else:
                    continue
                if send_date:
                    send_date = send_date[0]
                else:
                    send_date = None
                if send_date:
                    try:
                        send_date = parse(send_date)
                    except:
                        send_date = None

                results.append({'trigger': {'href': href, 'element': 'a'}, 'title': title, 'send_date': send_date,
                                'base_url': page_source.get('base_url')})

        return Result(results, False)
