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
from brain.utils.general import getDbMachine, compress_data, uncompress_data


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

        monkeypatch.delitem(os.environ, 'MANGA_LOCALHOST')
        monkeypatch.setitem(os.environ, 'HOSTNAME', hostname)
        if expname == 'utah' and not hostname:
            monkeypatch.setitem(os.environ, 'UUFSCELL', 'kingspeak.peaks')
        if expname == 'local' and not hostname:
            monkeypatch.setitem(os.environ, 'MANGA_LOCALHOST', '1')

        db = getDbMachine()
        assert db == expname


class TestCompression(object):
    ''' '''

    data = {'a': 1, 'b': 2, 'c': 3}

    @pytest.mark.parametrize('comptype, expcomp',
                             [('json', '{"a": 1, "c": 3, "b": 2}'),
                              ('msgpack', '\x83\xc4\x01a\x01\xc4\x01c\x03\xc4\x01b\x02')],
                             ids=['json', 'msgpack'])
    def test_compression(self, comptype, expcomp):
        comp = compress_data(self.data, compress_with=comptype)
        assert comp == expcomp

    @pytest.mark.parametrize('comptype, expcomp',
                             [('json', '{"a": 1, "c": 3, "b": 2}'),
                              ('msgpack', '\x83\xc4\x01a\x01\xc4\x01c\x03\xc4\x01b\x02')],
                             ids=['json', 'msgpack'])
    def test_uncompression(self, comptype, expcomp):
        comp = compress_data(self.data, compress_with=comptype)
        uncomp = uncompress_data(comp, uncompress_with=comptype)
        assert uncomp == self.data



