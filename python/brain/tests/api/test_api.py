# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2018-11-20 16:32:15
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2018-12-10 14:42:54

from __future__ import print_function, division, absolute_import

from brain import bconfig
from brain.api.api import BrainInteraction, BrainAuth
from brain.core.exceptions import BrainError
import pytest
import requests

auths = [None, 'token', 'netrc']


@pytest.fixture(params=auths)
def brainint(request):
    base = 'https://lore.sdss.utah.edu/test/'
    url = '/marvin/api/general/getroutemap/'
    ii = BrainInteraction(url, auth=request.param, send=False, base=base)
    yield ii
    ii = None


@pytest.fixture(scope='session')
def req():
    r = requests.get('https://data.sdss.org/sas/mangawork/manga/spectro/redux/v2_4_3/8485/stack/images/1901.png')
    yield r
    r = None


class TestBrainAuth(object):

    @pytest.mark.parametrize('auth', [(None), ('token'), ('netrc')])
    def test_init(self, auth):
        a = BrainAuth(authtype=auth)
        assert a.authtype == auth

    @pytest.mark.parametrize('auth, check',
                             [(None, None),
                              ('token', 'Bearer testtoken'),
                              ('netrc', 'Basic')], ids=['none', 'token', 'netrc'])
    def test_call(self, monkeypatch, req, auth, check):
        if auth == 'token':
            monkeypatch.setattr(bconfig, 'token', 'testtoken')

        a = BrainAuth(authtype=auth)
        resp = a(req)

        if not auth:
            assert 'Authorization' not in resp.headers
        else:
            assert 'Authorization' in resp.headers
            assert check in resp.headers['Authorization']


    def test_token_fail(self):
        a = BrainAuth(authtype='token')

        with pytest.raises(AssertionError) as cm:
            r = a(req)
        assert 'You must have a valid token set to use the API.  Please login.' in str(cm.value)


class TestInteraction(object):

    def test_auth(self, brainint):
        assert brainint.authtype in auths
        if brainint.authtype is None:
            assert brainint.session.auth is None
        else:
            assert brainint.authtype == brainint.session.auth.authtype


