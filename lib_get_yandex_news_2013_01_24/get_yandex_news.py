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

import sys, threading
from http import cookiejar
from urllib import request
from .html_parse import html_parse

DEFAULT_CONCURRENCY = 20

DEFAULT_URL_LIST = (
        'http://news.yandex.ru/',
        'http://news.yandex.ru/politics.html',
        'http://news.yandex.ru/world.html',
        'http://news.yandex.ru/society.html',
        'http://news.yandex.ru/business.html',
        'http://news.yandex.ru/sport.html',
        'http://news.yandex.ru/incident.html',
        'http://news.yandex.ru/culture.html',
        'http://news.yandex.ru/science.html',
        'http://news.yandex.ru/health.html',
        'http://news.yandex.ru/computers.html',
        'http://news.yandex.ru/internet.html',
        'http://news.yandex.ru/auto.html',
        'http://news.yandex.ru/travels.html',
        )

DEFAULT_TIMEOUT = 60.0
DEFAULT_CONTENT_LENGTH = 10000000

class GetYandexNewsError(Exception):
    pass

class Data:
    pass

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

def get_yandex_news_thread(get_lock, url_iter, on_begin=None, on_result=None):
    while True:
        data = Data()
        
        with get_lock:
            try:
                data.url_id, data.url = next(url_iter)
            except StopIteration:
                return
        
        if on_begin is not None:
            on_begin(data)
        
        try:
            cookies = cookiejar.CookieJar()
            opener = request.build_opener(
                    request.HTTPCookieProcessor(cookiejar=cookies),
                    )
            
            resp = ext_open(
                    opener,
                    data.url,
                    timeout=DEFAULT_TIMEOUT,
                    )
            if resp.getcode() != 200 or resp.geturl() != data.url:
                raise GetYandexNewsError(
                        'resp.getcode() != 200 or resp.geturl() != data.url')
            
            data.content = resp.read(DEFAULT_CONTENT_LENGTH).decode(
                    'utf-8', 'replace')
            
            result_list = []
            
            news_item_nodes = tuple(html_parse.find_tags(
                    (html_parse.html_parse(data.content),),
                    'dl',
                    attrs={
                            'class': 'b-news-item',
                            },
                    ))
            
            for news_item_node in news_item_nodes:
                result_item = {}
                
                news_title_nodes = tuple(html_parse.find_tags(
                        (news_item_node,),
                        'a',
                        attrs={
                                'class': 'title',
                                },
                        ))
                news_text_nodes = tuple(html_parse.find_tags(
                        (news_item_node,),
                        'dd',
                        attrs={
                                'class': 'text',
                                },
                        ))
                
                if news_title_nodes and \
                        news_title_nodes[0].childs and \
                        isinstance(news_title_nodes[0].childs[0], html_parse.DataHtmlNode):
                    result_item['title'] = news_title_nodes[0].childs[0].data
                
                if news_text_nodes and \
                        news_text_nodes[0].childs and \
                        isinstance(news_text_nodes[0].childs[0], html_parse.DataHtmlNode):
                    result_item['text'] = news_text_nodes[0].childs[0].data
                
                if result_item:
                    result_list.append(result_item)
            
            data.result = tuple(result_list)
            
        except Exception:
            data.error = sys.exc_info()
        else:
            data.error = None
        
        if on_result is not None:
            on_result(data)

def get_yandex_news(conc=None, url_list=None,
        on_begin=None, on_result=None, on_done=None):
    if conc is None:
        conc = DEFAULT_CONCURRENCY
    
    if url_list is None:
        url_list = DEFAULT_URL_LIST
    
    get_lock = threading.RLock()
    url_iter = enumerate(url_list)
    
    thread_list = tuple(
            threading.Thread(
                    target=lambda: get_yandex_news_thread(
                            get_lock,
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
