# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-02-19 23:37:44
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-02-20 00:24:45

from __future__ import print_function, division, absolute_import
import os
import pytest
import yaml
from brain.utils.general import (getDbMachine, compress_data, uncompress_data, merge,
                                 convertIvarToErr, inspection_authenticate,
                                 collaboration_authenticate, get_yaml_loader)


class TestGetDbMachine(object):
    ''' '''

    @pytest.mark.parametrize('expname, hostname',
                             [('local', 'manga'),
                              ('local', ''),
                              ('utah', 'sas-vm.sdss.org'),
                              ('utah', ''),
                              ('jhu', 'jhu.edu'),
                              (None, 'badmachine.org')],
                             ids=['local', 'local-2', 'sasvm', 'utah', 'jhu', 'none'])
    def test_servers(self, monkeypatch, expname, hostname):
        ''' test correct db name is returned '''

        if 'MANGA_LOCALHOST' in os.environ:
            monkeypatch.delitem(os.environ, 'MANGA_LOCALHOST')
        monkeypatch.setitem(os.environ, 'HOSTNAME', hostname)
        if expname == 'utah' and not hostname:
            monkeypatch.setitem(os.environ, 'UUFSCELL', 'kingspeak.peaks')
        if expname == 'local' and not hostname:
            monkeypatch.setitem(os.environ, 'MANGA_LOCALHOST', '1')
        if expname == 'jhu':
            monkeypatch.setitem(os.environ, 'SCISERVER', '1')

        db = getDbMachine()
        assert db == expname


class TestCompression(object):
    ''' '''

    data = {'a': 1, 'b': 2, 'c': 3}

    @pytest.mark.parametrize('comptype, expcomp',
                             [('json', '{"a": 1, "b": 2, "c": 3}'),
                              ('msgpack', b'\x83\xa1a\x01\xa1b\x02\xa1c\x03')],
                             ids=['json', 'msgpack'])
    def test_compression(self, comptype, expcomp):
        comp = compress_data(self.data, compress_with=comptype)
        assert comp == expcomp

    def test_base_compression(self):
        comp = compress_data(self.data)
        assert comp == '{"a": 1, "b": 2, "c": 3}'

    @pytest.mark.parametrize('comptype, expcomp',
                             [('json', '{"a": 1, "b": 2, "c": 3}'),
                              ('msgpack', b'\x83\xa1a\x01\xa1b\x02\xa1c\x03')],
                             ids=['json', 'msgpack'])
    def test_uncompression(self, comptype, expcomp):
        comp = compress_data(self.data, compress_with=comptype)
        assert comp == expcomp
        uncomp = uncompress_data(comp, uncompress_with=comptype)
        assert uncomp == self.data



def test_merge():
    data = merge({'a': 1, 'b': 2}, {'b': 3, 'c': 4})
    assert data == {'a': 1, 'b': 2, 'c': 4}


def test_convertivar():
    ivar = [127.242065, 122.203674, 123.58732 , 138.0441  , 133.99815 ,
            127.02346 , 125.417114, 123.45168 , 123.970924, 138.36519, 0., 0. ]
    exp = [0.08865121, 0.09046027, 0.08995246, 0.08511205, 0.08638744,
           0.08872746, 0.08929386, 0.09000186, 0.08981318, 0.08501324,
           0.        , 0.        ]
    data = convertIvarToErr(ivar)
    assert exp == pytest.approx(data)


def test_inspect_auth():
    data = inspection_authenticate({}, 'test', 'test')
    assert data == {'ready': True, 'message': 'Logged in as test. ',
                    'status': 1, 'membername': 'SDSS User', 'is_valid': True}

def test_collab_auth():
    data = collaboration_authenticate('test', 'test')
    assert data == {'is_valid': False, 'status': -1, 'message': "No module named 'collaboration'"}

def test_get_yaml():
    loader = get_yaml_loader()
    assert issubclass(loader, yaml.FullLoader)