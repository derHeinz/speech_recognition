#!/usr/bin/python3
# -*- coding: utf-8 -*-

import threading
import time
import queue

from softtone import SofttoneGenerator

class ToneGeneratorThread(object):
    
    def __init__(self):
        self.queue = queue.Queue()
        self.generator = SofttoneGenerator()
        self.thread = threading.Thread(name='ToneGenerator', target=self.run, daemon=True)
        self.thread.start()
        
    def _add(self, item):
        self.queue.put(item)
           
    def run(self):
        while True:
            if not self.queue.empty():
                item = self.queue.get_nowait()
                meth = getattr(self.generator, item)
                meth()
            time.sleep(0.2)

    def confirm(self):
        self._add("confirm")
        
    def abort(self):
        self._add("abort")

    def ready(self):
        self._add("ready")
