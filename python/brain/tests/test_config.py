# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-02-19 23:37:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-04-04 11:49:20

from __future__ import print_function, division, absolute_import
import pytest
import os
import sys

from brain import bconfig
from brain.core.exceptions import BrainError, BrainUserWarning

# Tests on Brain Config

@pytest.fixture()
def netrc(monkeypatch, tmpdir):
    tmpnet = tmpdir.mkdir('netrc').join('.netrc')
    monkeypatch.setattr(bconfig, '_netrc_path', str(tmpnet))
    yield tmpnet


@pytest.fixture()
def goodnet(netrc):
    netrc.write('')
    os.chmod(bconfig._netrc_path, 0o600)
    yield netrc


@pytest.fixture()
def bestnet(goodnet):
    goodnet.write(write('data.sdss.org'))
    goodnet.write(write('api.sdss.org'))
    yield goodnet


def write(host):
    netstr = 'machine {0}\n'.format(host)
    netstr += '    login test\n'
    netstr += '    password test\n'
    netstr += '\n'
    return netstr


class TestVars(object):
    ''' test getting/setting variables '''

    @pytest.mark.parametrize('var, toval',
                             [('mode', 'remote'), ('access', 'collab'), ('compression', 'msgpack')])
    def test_set(self, monkeypatch, var, toval):
        defval = bconfig.__getattribute__(var)
        assert defval != toval
        monkeypatch.setattr(bconfig, var, toval)
        newval = bconfig.__getattribute__(var)
        assert newval == toval

    @pytest.mark.parametrize('var, toval',
                             [('mode', 'super'), ('access', 'always'), ('compression', 'donut')])
    def test_set_wrong(self, var, toval):
        with pytest.raises(ValueError) as cm:
            bconfig.__setattr__(var, toval)
        assert 'config.{0} must be'.format(var) in str(cm.value)

    def test_bad_access(self, netrc):
        assert bconfig.access == 'public'
        with pytest.raises(BrainError) as cm:
            bconfig.access = 'collab'
        assert 'No .netrc file found in your HOME directory!' in str(cm.value)
        assert bconfig.access == 'public'


class TestNetrc(object):
    ''' test the netrc access '''

    def test_no_netrc(self, netrc):
        with pytest.raises(BrainError) as cm:
            bconfig._check_netrc()
        assert 'No .netrc file found in your HOME directory!' in str(cm.value)

    def test_badperm_netrc(self, netrc):
        netrc.write('')
        with pytest.raises(BrainError) as cm:
            bconfig._check_netrc()
        assert 'your .netrc file does not have 600 permissions.' in str(cm.value)

    @pytest.mark.parametrize('host, msg',
                             [('data.sdss.org', 'api.sdss.org not found in netrc. You will not have remote access to SDSS data'),
                              ('api.sdss.org', 'data.sdss.org not found in netrc. You will not be able to download SDSS data')],
                              ids=['noapi', 'nodata'])
    def test_only_one_host(self, goodnet, host, msg):
        goodnet.write(write(host))
        with pytest.warns(BrainUserWarning) as cm:
            bconfig._check_netrc()

        assert msg in str(cm[0].message)

    def test_good_netrc(self, bestnet):
        assert bconfig._check_netrc() is True

