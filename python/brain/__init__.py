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
        self._compression = 'json'
        self._compression_types = ['json', 'msgpack']

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, value):
        if value in ['local', 'remote', 'auto']:
            self._mode = value
        else:
            raise ValueError('config.mode must be "local" or "remote".')

    @property
    def compression(self):
        return self._compression

    @compression.setter
    def compression(self, value):
        if value in self._compression_types:
            self._compression = value
        else:
            raise ValueError('config.compression must be one of {0}.'.format(self._compression_types))

bconfig = BrainConfig()
