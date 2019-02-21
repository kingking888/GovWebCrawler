# @Time    : 2018/12/21 11:42 PM
# @Author  : SuanCaiYu
# @File    : main
# @Software: PyCharm
import os
import re
import traceback
import time
import pickle

from selenium import webdriver

from base.TurnPageConf import TurnPageConf
from settings import BROWSER_LOAD_IMG, BROWSER_DISK_CACHE, BROWSER_IGNORE_SLL_ERROR, BROWSER_BIN_PATH, \
    BROWSER_IMPLICITLY_WAIT, BROWSER_PAGELOAD_TIMEOUT, IS_TEST, TESE_CACHE_DIR, BROWSER_USER_AGENT, TURN_PAGE_WAIT
from utils.tools import url_join, get_md5

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class Browser(object):

    def __init__(self, timeout):
        if not timeout:
            timeout = BROWSER_PAGELOAD_TIMEOUT
        self.browser = self.__create_browser(timeout)
        self.test_cache_md5 = None
        self.test_cache = None

    def __create_browser(self, timeout):
        service_args, dcap = self.__get_config()
        browser = webdriver.PhantomJS(executable_path=BROWSER_BIN_PATH, service_args=service_args,
                                      desired_capabilities=dcap)
        browser.implicitly_wait(BROWSER_IMPLICITLY_WAIT)
        browser.set_page_load_timeout(timeout)
        browser.set_window_size(1024, 768)
        return browser

    def __get_config(self):
        service_args = []
        if not BROWSER_LOAD_IMG:
            service_args.append('--load-images=no')
        if BROWSER_DISK_CACHE:
            service_args.append('--disk-cache=yes')
        if BROWSER_IGNORE_SLL_ERROR:
            service_args.append('--ignore-ssl-errors=true')
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = BROWSER_USER_AGENT
        return service_args, dcap

    def load(self, url):
        self.test_cache_md5 = get_md5(url)
        if os.path.exists(os.path.join(TESE_CACHE_DIR, f'{self.test_cache_md5}.cache')) and IS_TEST:
            with open(os.path.join(TESE_CACHE_DIR, f'{self.test_cache_md5}.cache'), 'rb') as fp:
                self.test_cache = pickle.load(fp, encoding="utf8")
        else:
            self.browser.get(url)
            time.sleep(TURN_PAGE_WAIT)

    def get_html(self, is_list=True):
        if is_list:
            return [{'base_url': self.get_base_href(), 'source': self.browser.page_source}]
        else:
            return {'base_url': self.get_base_href(), 'source': self.browser.page_source}

    def get_base_href(self):
        try:
            base_tag = self.browser.find_element_by_tag_name("base")
            url = None
            if base_tag:
                url = base_tag.get_attribute('href')
                url = url_join(self.browser.current_url, url)
        except:
            url = None
        if not url:
            url = self.browser.current_url
        return url

    def get_all_iframe_html(self):
        if IS_TEST and self.test_cache_md5 and os.path.exists(
                os.path.join(TESE_CACHE_DIR, f'{self.test_cache_md5}.cache')):
            return self.test_cache
        else:
            page_sources = [self.get_html(is_list=False)]
            iframes = self.browser.find_elements_by_tag_name('iframe')
            for iframe in iframes:
                self.browser.switch_to.frame(iframe)
                page_sources.append(self.get_html(is_list=False))
                self.browser.switch_to.default_content()
            if self.test_cache_md5:
                with open(os.path.join(TESE_CACHE_DIR, f'{self.test_cache_md5}.cache'), 'wb') as fp:
                    pickle.dump(page_sources, fp)
            return page_sources

    def save_page_screenshot(self, file_name):
        self.browser.save_screenshot(file_name)

    def get_page_screenshot_as_base64(self):
        return self.browser.get_screenshot_as_base64()

    def quit(self):
        self.browser.quit()

    def get_log(self, key):
        if self.test_cache_md5 and IS_TEST and self.test_cache:
            return 'test'
        return self.browser.get_log(key)

    def turn_page(self, turn_page_conf: TurnPageConf, logger):
        if IS_TEST:
            logger.info(f'测试环境,获取到翻页参数:{str(turn_page_conf)}')
            return False
        flag = self.__turn_action(turn_page_conf)
        if flag: return flag
        try:
            iframes = self.browser.find_elements_by_tag_name('iframe')
        except Exception as e:
            logger.info(f'翻页查找iframe错误{repr(e)}')
            return False
        for iframe in iframes:
            if flag:
                return flag
            self.browser.switch_to.frame(iframe)
            flag = self.__turn_action(turn_page_conf)
            self.browser.switch_to.default_content()
        return flag

    def __turn_action(self, turn_page_conf: TurnPageConf):
        try:
            if turn_page_conf.xpath:
                if turn_page_conf.tag_name == 'a':
                    tag = self.browser.find_element_by_xpath(turn_page_conf.xpath)
                else:
                    tags = self.browser.find_elements_by_xpath(turn_page_conf.xpath)
                    for _tag in tags:
                        if _tag.text == turn_page_conf.text:
                            tag = _tag
                            break
                    else:
                        tag = None
            elif turn_page_conf.text and (turn_page_conf.tag_name == 'a'):
                tag = self.browser.find_element_by_link_text(turn_page_conf.text)
            else:
                tag = None
            if tag:
                tag.click()
                time.sleep(TURN_PAGE_WAIT)
                self.save_page_screenshot(f'./images/{turn_page_conf.page_num}.png')
                return True
            else:
                return False
        except Exception as e:
            return False

    def find_tag(self, xpath):
        try:
            tag = self.browser.find_element_by_xpath(xpath)
        except:
            tag = None
        if tag:
            return tag
        iframes = self.browser.find_elements_by_tag_name('iframe')
        for iframe in iframes:
            self.browser.switch_to.frame(iframe)
            try:
                tag = self.browser.find_element_by_xpath(xpath)
            except:
                self.browser.switch_to.default_content()
                continue
            if tag:
                return tag
            self.browser.switch_to.default_content()
        return None

    def get_content_html(self, xpath):
        current_handle = self.browser.current_window_handle
        current_url = self.browser.current_url
        all_handle = self.browser.window_handles
        tag = self.find_tag(xpath)
        if tag:
            tag.click()
            time.sleep(2)
            self.browser.switch_to.default_content()
        else:
            print(f'通过{xpath}未获得元素')
        current_all_handle = self.browser.window_handles
        if len(all_handle) < len(current_all_handle):
            # 打开了新的窗口
            return self.open_new_window(current_handle, all_handle, current_all_handle)
        elif current_url != self.browser.current_url:
            # 在本窗口打开链接
            return self.open_of_current_window()
        else:
            # 在本窗口弹窗
            return self.alert_show()

    def open_new_window(self, current_handle, all_handle, current_all_handle):
        use_handle = None
        for handle in current_all_handle:
            for _handle in all_handle:
                if handle == _handle:
                    break
            else:
                use_handle = handle
                break
        if use_handle:
            self.browser.switch_to_window(use_handle)
        else:
            return
        self.browser.execute_script('window.stop();')

        html = self.get_all_iframe_html()
        img_base64 = self.get_page_screenshot_as_base64()

        self.browser.close()
        self.browser.switch_to_window(current_handle)
        return html, img_base64

    def alert_show(self):
        if re.match(r'.*zxts\.[a-z]*\.gov\.cn/sun/.*|.*www\.zjzxts\.gov\.cn/sun/.*', self.browser.current_url):
            iframe = self.browser.find_element_by_tag_name('iframe')
            if iframe:
                self.browser.switch_to.frame(iframe)
            html = self.browser.page_source
            img_base64 = self.get_page_screenshot_as_base64()
            if iframe:
                self.browser.switch_to.default_content()
            self.browser.find_element_by_css_selector('.layui-layer-ico.layui-layer-close.layui-layer-close2').click()
            time.sleep(1.5)
            return html, img_base64
        elif 'govmail.qingdao.gov.cn' in self.browser.current_url:
            tag = self.find_tag_css(self.browser, '.xubox_close.xulayer_png32.xubox_close0')
            if tag:
                tag.click()
            self.browser.switch_to.default_content()
            time.sleep(1.5)
        elif re.match('.*linxiaxian\.gov\.cn.*|.*lxs\.gov\.cn.*|.*http://www\.hezheng\.gov\.cn.*',
                      self.browser.current_url):
            html = self.browser.page_source
            img_base64 = self.get_page_screenshot_as_base64()
            self.browser.find_element_by_css_selector('.layui-layer-ico.layui-layer-close.layui-layer-close1').click()
            time.sleep(1.5)
            return html, img_base64
        elif 'www.gdqy.gov.cn' in self.browser.current_url:
            iframes = self.browser.find_elements_by_tag_name('iframe')
            for _iframe in iframes:
                self.browser.switch_to.frame(_iframe)
                if '/frontapp/wsxf/index_wsxf_getSLQK.jsp' in self.browser.current_url:
                    break
                self.browser.switch_to.default_content()
            html = self.browser.page_source
            img_base64 = self.get_page_screenshot_as_base64()
            self.browser.switch_to.default_content()
            self.browser.find_element_by_css_selector('a.ui_close').click()
            time.sleep(1.5)
            return html, img_base64
        elif 'fcms.feicheng.gov.cn' in self.browser.current_url:
            html = self.browser.page_source
            img_base64 = self.get_page_screenshot_as_base64()
            self.browser.find_element_by_css_selector('a.closeBtn').click()
            time.sleep(1.5)
            return html, img_base64
        elif 'zwzx.bynr.gov.cn' in self.browser.current_url:
            tag = self.find_tag_css(self.browser, 'span.close')
            if tag:
                tag.click()
            self.browser.switch_to.default_content()
            time.sleep(1.5)
            pass

    def find_tag_css(self, browser, css):
        try:
            tag = browser.find_element_by_css_selector(css)
        except:
            tag = None
        if tag:
            return tag
        iframes = browser.find_elements_by_tag_name('iframe')
        for iframe in iframes:
            browser.switch_to.frame(iframe)
            try:
                tag = browser.find_element_by_css_selector(css)
            except:
                browser.switch_to.default_content()
                continue
            if tag:
                return tag
            browser.switch_to.default_content()
        return None

    def open_of_current_window(self):
        html = self.get_all_iframe_html()
        img_base64 = self.get_page_screenshot_as_base64()
        self.browser.back()
        time.sleep(3)
        return html, img_base64
