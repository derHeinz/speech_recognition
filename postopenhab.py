#!/usr/bin/python3
# -*- coding: utf-8 -*-

from urllib.request import urlopen, build_opener, HTTPHandler, Request
import datetime

def _get_baseurl():
    return 'http://localhost:8080/rest/items/'

def _params_from_value(value):
    if isinstance(value, datetime.datetime):
        time_string = value.strftime("%Y-%m-%dT%H:%M:%S")
        return time_string.encode('utf-8')
    else:
        return value.encode('utf-8')
    
def post_value_to_openhab(itemname, value, base_url=_get_baseurl()):
    # construct URL
    url = base_url + itemname
    # need to have this header all other headers are ignored!
    header = {"Content-Type":"text/plain"}
    params_bytes = _params_from_value(value)
    req = Request(url, params_bytes, header)
    response = urlopen(req)
    