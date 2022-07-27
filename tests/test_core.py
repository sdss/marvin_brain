#!/usr/bin/env python
# encoding: utf-8

import pytest
from brain.core.core import URLMapDict
from brain.core.exceptions import BrainError


def test_urlmap():
    data = {'a':1, 'b':2, 'c':[1,2,3], 'd': {'e': 1, 'f': 2}}
    out = URLMapDict(data)
    assert out == data


def test_urlmap_missing():
    data = {'a':1, 'b':2, 'c':[1,2,3], 'd': {'e': 1, 'f': 2}}
    out = URLMapDict(data)
    with pytest.raises(BrainError, match='Key new not found in urlmap'):
        out['new']


def test_urlmap_empty():
    out = URLMapDict({})
    with pytest.raises(BrainError, match='No URL Map found. Cannot make remote call'):
        out['new']

