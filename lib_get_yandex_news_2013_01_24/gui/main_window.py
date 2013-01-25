#!/usr/bin/env python3
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

import threading
import tkinter
from tkinter import ttk, scrolledtext
from . import tk_mt
from .. import get_yandex_news

DEFAULT_MAIN_WINDOW_WIDTH = 700
DEFAULT_MAIN_WINDOW_HEIGHT = 500

class MainWindow:
    def __init__(self):
        self._root = tkinter.Tk()
        self._tk_mt = tk_mt.TkMt(self._root)
        self._root.protocol("WM_DELETE_WINDOW", self._close_cmd)
        
        self._root.title(string='get-yandex-news-gui')
        self._root.geometry('{}x{}'.format(
                DEFAULT_MAIN_WINDOW_WIDTH, DEFAULT_MAIN_WINDOW_HEIGHT))
        
        self._menubar = tkinter.Menu(master=self._root)
        self._program_menu = tkinter.Menu(master=self._menubar)
        self._program_menu.add_command(label="Load / Reload", command=self._reload_cmd)
        self._program_menu.add_command(label="Copy", command=self._copy_cmd)
        self._program_menu.add_separator()
        self._program_menu.add_command(label="Close", command=self._close_cmd)
        self._menubar.add_cascade(label="Program", menu=self._program_menu)
        self._root.config(menu=self._menubar)
        
        self._text = scrolledtext.ScrolledText(master=self._root)
        self._text.config(state=tkinter.DISABLED)
        
        self._reload_button = ttk.Button(master=self._root,
                text='Load / Reload',
                command=self._reload_cmd)
        self._copy_button = ttk.Button(master=self._root,
                text='Copy',
                command=self._copy_cmd)
        self._close_button = ttk.Button(master=self._root,
                text='Close',
                command=self._close_cmd)
        
        self._text.pack(fill=tkinter.BOTH, expand=True)
        self._reload_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._copy_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._close_button.pack(side=tkinter.RIGHT, padx=10, pady=10)
        
        self._busy_state = False
        self._busy_state_id = object()
    
    def _close_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        self._tk_mt.push_destroy()
    
    def _reload_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        self._busy_state = True
        self._busy_state_id = object()
        
        self._text.config(state=tkinter.NORMAL)
        self._text.delete(1.0, tkinter.END)
        self._text.config(state=tkinter.DISABLED)
        
        def on_result(busy_state_id, data):
            self._tk_mt.push(lambda: self._on_reload_result(busy_state_id, data))
        
        def on_done(busy_state_id):
            self._tk_mt.push(lambda: self._on_reload_done(busy_state_id))
        
        get_yandex_news.get_yandex_news(
                on_result=lambda data, _busy_state_id=self._busy_state_id:
                        on_result(_busy_state_id, data),
                on_done=lambda _busy_state_id=self._busy_state_id:
                        on_done(_busy_state_id),
                )
    
    def _on_reload_result(self, busy_state_id, data):
        if busy_state_id != self._busy_state_id:
            return
        
        if data.error is not None:
            return
        
        self._text.config(state=tkinter.NORMAL)
        for result in data.result:
            try:
                result_title = result['title']
            except KeyError:
                pass
            else:
                self._text.insert(tkinter.END, '{}\n'.format(result_title))
        self._text.config(state=tkinter.DISABLED)
    
    def _on_reload_done(self, busy_state_id):
        if busy_state_id != self._busy_state_id:
            return
        
        self._busy_state = False
        self._busy_state_id = object()
    
    def _copy_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        content = self._text.get(1.0, tkinter.END).rstrip()
        self._root.clipboard_clear()
        self._root.clipboard_append(content)
