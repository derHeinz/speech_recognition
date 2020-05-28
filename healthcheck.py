#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import threading

class HealthCheck(object):
    
    def __init__(self, port):
        self.port = port
        self.app = Flask(__name__)
        self.app.add_url_rule(rule="/health", view_func=self.health, methods=['GET'])

    def start(self):
        threading.Thread(target=self.app.run, kwargs={'host':'0.0.0.0', 'port':self.port}, daemon=True).start()
        print("Starting %s on port %d" % ("healthcheck",  self.port))
        
    def health(self):
        
        res = {"status": "ok"}
        return jsonify(res)
