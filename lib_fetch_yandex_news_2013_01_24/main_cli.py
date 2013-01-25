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

import threading, argparse
from . import read_list, fetch_yandex_news

class UserError(Exception):
    pass

def on_begin(ui_lock, data):
    with ui_lock:
        print('[{!r}] begin: {!r}'.format(data.url_id, data.url))

def on_result(ui_lock, out_fd, data):
    with ui_lock:
        if data.error is not None:
            print('[{!r}] error: {!r}: {!r}: {!r}'.format(
                    data.url_id, data.url,
                    data.error[0], data.error[1]))
            return
        
        for result_line in fetch_yandex_news.result_line_format(data):
            out_fd.write('{}\n'.format(result_line))
        out_fd.flush()
        
        print('[{!r}] pass: {!r}'.format(data.url_id, data.url))

def on_done(ui_lock, done_event):
    with ui_lock:
        print('done!')
        done_event.set()

def main():
    parser = argparse.ArgumentParser(
            description='utility for fetching news titles from ``Yandex.News``.',
            )
    parser.add_argument(
            '--urls',
            metavar='URL-LIST-PATH',
            help='path to url list file',
            )
    parser.add_argument(
            '--out',
            metavar='OUTPUT-PATH',
            help='path to output result file',
            )
    args = parser.parse_args()
    
    if args.out is None:
        raise UserError('args.out is None')
    
    ui_lock = threading.RLock()
    
    if args.urls is not None:
        url_list = read_list.read_list(args.urls)
    else:
        url_list = None
    
    with open(args.out, 'w', encoding='utf-8', errors='replace', newline='\n') as out_fd:
        done_event = threading.Event()
        fetch_yandex_news.fetch_yandex_news(
                url_list=url_list,
                on_begin=lambda data: on_begin(ui_lock, data),
                on_result=lambda data: on_result(ui_lock, out_fd, data),
                on_done=lambda: on_done(ui_lock, done_event),
                )
        done_event.wait()
