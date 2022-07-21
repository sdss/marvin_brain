# !usr/bin/env python
# -*- coding: utf-8 -*-
#


from brain.utils.general.decorators import parseRoutePath, public, check_auth, checkPath


def fakefunc(*args, **kwargs):
    return kwargs


def test_public():
    tt = public(fakefunc)
    assert hasattr(tt, 'is_public')
    assert tt.is_public is True


def test_checkPath():
    tt = checkPath(fakefunc)()
    assert tt == {}


def test_parseRoute():
    kwargs = {'a': 1, 'b': 2, 'path': 'a=b/c=d/e=f'}
    kk = parseRoutePath(fakefunc)(None, **kwargs)
    assert kk == {'a': 'b', 'b': 2, 'c': 'd', 'e': 'f'}


def test_check_auth():
    tt = check_auth(fakefunc)()
    assert tt == {}
