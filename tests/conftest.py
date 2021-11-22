# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-02-19 23:37:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-02-19 23:39:32

from __future__ import print_function, division, absolute_import

import os
import pytest
from brain import bconfig


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