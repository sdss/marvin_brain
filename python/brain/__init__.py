#!/usr/bin/env python
# encoding: utf-8
#
# __init__.py
#
# Licensed under a 3-clause BSD license.
#

from __future__ import division
from __future__ import print_function
import os


class BrainConfig(object):

    def __init__(self):

        self.sasurl = os.getenv('SAS_URL') if 'SAS_URL' in os.environ else 'https://sas.sdss.org/'
        self._mode = 'auto'
        self.session_id = None
        self.request_session = None
        self.traceback = None

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value in ['local', 'remote', 'auto']:
            self._mode = value
        else:
            raise ValueError('config.mode must be "local" or "remote".')

bconfig = BrainConfig()
