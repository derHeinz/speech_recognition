#!/usr/bin/python3
# -*- coding: utf-8 -*-

import wiringpi

class SofttoneGenerator(object):
    
    PIN = 3

    ABORT = [350, 0, 150, 150, 0]
    CONFIRM = [1200, 1200, 0, 900, 0]
    READY = [1500, 0, 800, 0]

    def __init__(self):
        wiringpi.wiringPiSetup()
        wiringpi.softToneCreate(self.PIN)
        
    def _play(self, arr):
        for idx in arr:
            wiringpi.softToneWrite(self.PIN, idx)
            wiringpi.delay(50)
        
    def confirm(self):
        self._play(self.CONFIRM)
        
    def abort(self):
        self._play(self.ABORT)

    def ready(self):
        self._play(self.READY)
