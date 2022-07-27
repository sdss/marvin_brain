# !usr/bin/env python
# -*- coding: utf-8 -*-
#

from werkzeug.test import EnvironBuilder
from flask import Request

from brain.api.base import processRequest


def test_process_get():
    ee = EnvironBuilder(method='GET', path='get',
                        base_url='https://httpbin.org', query_string='a=1&b=2')
    rr = Request(ee.get_environ())
    out = processRequest(rr)
    assert out.to_dict() == {'a': '1', 'b': '2'}

def test_process_get_param():
    ee = EnvironBuilder(method='GET', path='get',
                        base_url='https://httpbin.org', query_string='a=1&b=2')
    rr = Request(ee.get_environ())
    out = processRequest(rr, param='a')
    assert out == '1'


def test_process_post_json():
    ee = EnvironBuilder(method='POST', path='post',
                        base_url='https://httpbin.org', json={'a':1, 'b':2})
    rr = Request(ee.get_environ())
    out = processRequest(rr, as_dict=True)
    assert out == {'a': 1, 'b': 2}

def test_process_post_form():
    ee = EnvironBuilder(method='POST', path='post',
                        base_url='https://httpbin.org', data={'a':1, 'b':2})
    rr = Request(ee.get_environ())
    out = processRequest(rr, as_dict=True)
    assert out.to_dict() == {'a': '1', 'b': '2'}
