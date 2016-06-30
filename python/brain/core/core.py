#!/usr/bin/env python
# encoding: utf-8
#
# file.py
#
# Licensed under a 3-clause BSD license.
#
# Revision history:
#    21 Apr 2016 J. Sánchez-Gallego
#       Initial version


from __future__ import division
from __future__ import print_function
from brain.core.exceptions import BrainError


class URLMapDict(dict):
    """A custom dictionary for urlmap that fails with a custom error."""

    def __init__(self, inp={}):
        self.update(**dict((kk, self.parse(vv)) for kk, vv in inp.items()))

    @classmethod
    def parse(cls, vv):
        if isinstance(vv, dict):
            return cls(vv)
        elif isinstance(vv, list):
            return [cls.parse(ii) for ii in vv]
        else:
            return vv

    def __missing__(self, key):
        """Overrides the default KeyError exception."""

        if len(self.keys()) == 0:
            raise BrainError('No URL Map found. Cannot make remote call')
        else:
            raise BrainError('Key {0} not found in urlmap.'.format(key))
