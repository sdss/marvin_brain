# !usr/bin/env python
# -*- coding: utf-8 -*-
#

from brain.api.query import BrainQueryView
from brain.api.general import BrainGeneralRequestsView


def test_query():
    b = BrainQueryView()
    assert b.route_base == '/query/'


def test_general():
    b = BrainGeneralRequestsView()
    assert b.route_base == '/general/'


