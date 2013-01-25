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

import sys
import threading
import queue

TK_PULL_DELAY = 100 # milliseconds

DESTROY = object()

# this is Multi-Thread support for Tk
class TkMt:
    def __init__(self, root):
        self._root = root
        self._queue = queue.Queue()
        self._closed = False
        
        self._root.after(TK_PULL_DELAY, self._pull_handle)
    
    def close(self):
        self._closed = True
    
    def _pull_handle(self):
        if self._closed:
            return
        
        while True:
            try:
                f = self._queue.get_nowait()
            except queue.Empty:
                break
            else:
                try:
                    if f == DESTROY:
                        self.close()
                        self._root.destroy()
                        return
                    
                    self._root.after_idle(f)
                finally:
                    self._queue.task_done()
        
        self._root.after(TK_PULL_DELAY, self._pull_handle)
    
    # threadsafe function
    def push(self, callback):
        if self._closed:
            return
        
        assert callable(callback) or callback == DESTROY
        
        self._queue.put(callback)
    
    # threadsafe function
    def push_destroy(self):
        self.push(DESTROY)
    
    # threadsafe function
    def start_daemon(self, thread_target, callback=None):
        assert callback is None or callable(callback)
        
        def _thread_target():
            result = None
            error = None
            
            try:
                result = thread_target()
            except:
                error = sys.exc_info()
            
            if callback is not None:
                self.push(lambda: callback(result, error))
        
        thread = threading.Thread(target=_thread_target)
        thread.daemon = True
        
        self.push(thread.start)
