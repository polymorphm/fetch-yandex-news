# -*- mode: python; coding: utf-8 -*-
#
# Copyright 2013 Andrej A Antonov <polymorphm@gmail.com>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

assert str is not bytes

import sys, threading, re
from http import cookiejar
from urllib import request
from urllib import parse as url_parse
from .lib_html_parse import html_parse

DEFAULT_CONCURRENCY = 20

DEFAULT_URL_LIST = (
        'http://news.yandex.ru/politics.html',
        'http://news.yandex.ru/world.html',
        'http://news.yandex.ru/society.html',
        'http://news.yandex.ru/business.html',
        'http://news.yandex.ru/sport.html',
        'http://news.yandex.ru/energy.html',
        'http://news.yandex.ru/metallurgy.html',
        'http://news.yandex.ru/transport.html',
        'http://news.yandex.ru/insurance.html',
        'http://news.yandex.ru/realty.html',
        'http://news.yandex.ru/football.html',
        'http://news.yandex.ru/hockey.html',
        'http://news.yandex.ru/basketball.html',
        'http://news.yandex.ru/tennis.html',
        'http://news.yandex.ru/auto_racing.html',
        'http://news.yandex.ru/martial_arts.html',
        'http://news.yandex.ru/incident.html',
        'http://news.yandex.ru/culture.html',
        'http://news.yandex.ru/music.html',
        'http://news.yandex.ru/theaters.html',
        'http://news.yandex.ru/galleries.html',
        'http://news.yandex.ru/science.html',
        'http://news.yandex.ru/health.html',
        'http://news.yandex.ru/computers.html',
        'http://news.yandex.ru/security.html',
        'http://news.yandex.ru/software.html',
        'http://news.yandex.ru/hardware.html',
        'http://news.yandex.ru/mobile.html',
        'http://news.yandex.ru/internet.html',
        'http://news.yandex.ru/games.html',
        'http://news.yandex.ru/auto.html',
        'http://news.yandex.ru/travels.html',
        )

DEFAULT_TIMEOUT = 60.0
DEFAULT_CONTENT_LENGTH = 10000000

class FetchNewsError(Exception):
    pass

class FetchYandexNewsError(FetchNewsError):
    pass

class UnknownServiceFetchNewsError(FetchNewsError):
    pass

class Data:
    pass

def result_line_format(data, show_url=None, url_seporator=None):
    if show_url is None:
        show_url = False
    
    for result in data.result:
        try:
            result_title = result['title']
        except KeyError:
            result_title = None
        
        try:
            result_url = result['url']
        except KeyError:
            result_url = None
        
        if result_title is None:
            continue
        
        if show_url:
            if result_url is None:
                continue
            
            if url_seporator is not None:
                yield '{}{}{}'.format(
                        str(result_title).replace('\n', ' ... ').replace(url_seporator, ' ... '),
                        url_seporator,
                        str(result_url).replace('\n', ' ... ').replace(url_seporator, ' ... '),
                        )
            else:
                yield '{} {}'.format(
                        str(result_title).replace('\n', ' ... '),
                        str(result_url).replace('\n', ' ... '),
                        )
            
            continue
        
        yield str(result_title).replace('\n', ' ... ')

def ext_open(opener, *args,
        headers=None, new_headers=None,
        **kwargs):
    if headers is not None:
        spec_headers = headers
    else:
        spec_headers = opener.addheaders
    
    if new_headers is not None:
        spec_headers = list(spec_headers)
        spec_headers += new_headers
    
    orig_headers = opener.addheaders
    opener.addheaders = spec_headers
    try:
        resp = opener.open(*args, **kwargs)
    finally:
        opener.addheaders = orig_headers
    
    return resp

def fix_yandex_news_url(raw_url):
    raw_url_obj = url_parse.urlsplit(raw_url)
    raw_url_query = raw_url_obj.query
    
    if not raw_url_query:
        return str(raw_url)
    
    raw_url_params = url_parse.parse_qs(raw_url_query)
    cl4url_param = raw_url_params.get('cl4url', [''])[0]
    
    if not cl4url_param:
        return str(raw_url)
    
    if not url_parse.urlparse(cl4url_param).scheme:
        cl4url_param = 'http://{}'.format(cl4url_param)
    
    return cl4url_param

def parse_yandex_news(url):
    cookies = cookiejar.CookieJar()
    opener = request.build_opener(
            request.HTTPCookieProcessor(cookiejar=cookies),
            )
    
    resp = ext_open(
            opener,
            url,
            timeout=DEFAULT_TIMEOUT,
            )
    if resp.getcode() != 200 or resp.geturl() != url:
        raise FetchYandexNewsError(
                'resp.getcode() != 200 or resp.geturl() != url')
    
    content = resp.read(DEFAULT_CONTENT_LENGTH).decode(
            'utf-8', 'replace')
    
    result_list = []
    
    news_item_nodes = tuple(html_parse.find_tags(
            (html_parse.html_parse(content, use_min_attr_hack=True),),
            'dl',
            in_attrs={
                    'class': 'b-news-item',
                    },
            ))
    
    for news_item_node in news_item_nodes:
        result_item = {}
        
        news_title_nodes = tuple(html_parse.find_tags(
                (news_item_node,),
                'a',
                in_attrs={
                        'class': 'title',
                        },
                ))
        news_text_nodes = tuple(html_parse.find_tags(
                (news_item_node,),
                'dd',
                in_attrs={
                        'class': 'text',
                        },
                ))
        
        if not news_title_nodes or \
                not news_title_nodes[0].childs or \
                not isinstance(news_title_nodes[0].childs[0], html_parse.DataHtmlNode):
            continue
        
        result_item['title'] = news_title_nodes[0].childs[0].data
        result_item['raw_url'] = url_parse.urljoin(url, news_title_nodes[0].attrs.get('href', ''))
        result_item['url'] = fix_yandex_news_url(result_item['raw_url'])
        
        if news_text_nodes and \
                news_text_nodes[0].childs and \
                isinstance(news_text_nodes[0].childs[0], html_parse.DataHtmlNode):
            result_item['text'] = news_text_nodes[0].childs[0].data
        
        if result_item:
            result_list.append(result_item)
    
    return tuple(result_list)

def fetch_news_thread(fetch_lock, url_iter, on_begin=None, on_result=None):
    while True:
        data = Data()
        
        with fetch_lock:
            try:
                data.url_id, data.url = next(url_iter)
            except StopIteration:
                return
        
        if on_begin is not None:
            on_begin(data)
        
        try:
            if re.match(
                    '^https?\:\/\/news\.yandex\.ru(\/|$)',
                    data.url, flags=re.M|re.S):
                data.result = parse_yandex_news(data.url)
            else:
                raise UnknownServiceFetchNewsError(
                        'unknown service')
        except Exception:
            data.error = sys.exc_info()
        else:
            data.error = None
        
        if on_result is not None:
            on_result(data)

def fetch_news(conc=None, url_list=None,
        on_begin=None, on_result=None, on_done=None):
    if conc is None:
        conc = DEFAULT_CONCURRENCY
    
    if url_list is None:
        url_list = DEFAULT_URL_LIST
    
    fetch_lock = threading.RLock()
    url_iter = enumerate(url_list)
    
    thread_list = tuple(
            threading.Thread(
                    target=lambda: fetch_news_thread(
                            fetch_lock,
                            url_iter,
                            on_begin=on_begin,
                            on_result=on_result,
                            ),
                    )
            for thread_i in range(conc)
            )
    
    for thread in thread_list:
        thread.start()
    
    def in_thread():
        for thread in thread_list:
            thread.join()
        
        if on_done is not None:
            on_done()
    
    threading.Thread(target=in_thread).start()
