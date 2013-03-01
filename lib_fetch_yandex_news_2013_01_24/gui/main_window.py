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
from .. import fetch_news

DEFAULT_MAIN_WINDOW_WIDTH = 700
DEFAULT_MAIN_WINDOW_HEIGHT = 500

class MainWindow:
    def __init__(self):
        self._root = tkinter.Tk()
        self._tk_mt = tk_mt.TkMt(self._root)
        self._root.protocol("WM_DELETE_WINDOW", self._close_cmd)
        
        self._root.title(string='fetch-yandex-news-gui')
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
        
        self._show_url_var = tkinter.BooleanVar()
        self._show_url = ttk.Checkbutton(
                master=self._root, variable=self._show_url_var, text='Show URL')
        
        self._status_var = tkinter.StringVar()
        self._statusbar = ttk.Label(master=self._root,
                textvariable=self._status_var)
        
        self._text.pack(fill=tkinter.BOTH, expand=True)
        self._reload_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._copy_button.pack(side=tkinter.LEFT, padx=10, pady=10)
        self._show_url.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self._statusbar.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        self._close_button.pack(side=tkinter.RIGHT, padx=10, pady=10)
        
        self._busy_state = False
        self._busy_state_id = object()
        self._set_status('Ready')
    
    def _close_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        self._tk_mt.push_destroy()
    
    def _set_status(self, text):
        self._status_var.set('Status: {}'.format(text))
    
    def _reload_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        self._busy_state = True
        self._busy_state_id = object()
        self._set_status('Working')
        
        self._reload_button.config(state=tkinter.DISABLED)
        self._copy_button.config(state=tkinter.DISABLED)
        self._show_url.config(state=tkinter.DISABLED)
        self._close_button.config(state=tkinter.DISABLED)
        
        self._text.config(state=tkinter.NORMAL)
        self._text.delete(1.0, tkinter.END)
        self._text.config(state=tkinter.DISABLED)
        
        busy_state_id = self._busy_state_id
        show_url = self._show_url_var.get()
        
        def on_result(data):
            self._tk_mt.push(lambda: self._on_reload_result(busy_state_id, show_url, data))
        
        def on_done():
            self._tk_mt.push(lambda: self._on_reload_done(busy_state_id))
        
        fetch_news.fetch_news(
                on_result=on_result,
                on_done=on_done,
                )
    
    def _on_reload_result(self, busy_state_id, show_url, data):
        if busy_state_id != self._busy_state_id:
            return
        
        if data.error is not None:
            return
        
        self._text.config(state=tkinter.NORMAL)
        for result_line in fetch_news.result_line_format(data, show_url=show_url):
            self._text.insert(tkinter.END, '{}\n'.format(result_line))
        self._text.config(state=tkinter.DISABLED)
    
    def _on_reload_done(self, busy_state_id):
        if busy_state_id != self._busy_state_id:
            return
        
        self._busy_state = False
        self._busy_state_id = object()
        self._set_status('Done')
        
        self._reload_button.config(state=tkinter.NORMAL)
        self._copy_button.config(state=tkinter.NORMAL)
        self._show_url.config(state=tkinter.NORMAL)
        self._close_button.config(state=tkinter.NORMAL)
    
    def _copy_cmd(self):
        if self._busy_state:
            self._root.bell()
            return
        
        content = self._text.get(1.0, tkinter.END).rstrip()
        self._root.clipboard_clear()
        self._root.clipboard_append(content)
