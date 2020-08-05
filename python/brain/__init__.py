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
import netrc
import warnings
import yaml
from brain.core.exceptions import BrainError, BrainUserWarning
from brain.utils.general.general import merge, get_yaml_loader

# Set the Brain version
__version__ = '0.1.4dev'


class BrainConfig(object):

    def __init__(self):

        self._mode = 'auto'
        self.session_id = None
        self.request_session = None
        self.traceback = None
        self._compression = 'json'
        self._compression_types = ['json', 'msgpack']
        self._access = 'public'
        self._access_types = ['public', 'collab']
        self._netrc_path = os.path.join(os.path.expanduser('~'), '.netrc')
        self._netrc = None
        self.hosts = ['data.sdss.org', 'api.sdss.org', 'magrathea.sdss.org']
        self.mirrors = ['magrathea.sdss.org']
        self._valid_hosts = dict.fromkeys(self.hosts)
        self.token = None

        self._load_defaults()
        self._check_paths()
        self._set_api_urls()


    @property
    def public_api_url(self):
        return self._public_api_url

    @property
    def collab_api_url(self):
        return self._collab_api_url

    @property
    def mirror_api_url(self):
        return self._mirror_api_url

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

    @property
    def access(self):
        return self._access

    @access.setter
    def access(self, value):
        if value in self._access_types:
            if value == 'collab':
                if not self._check_netrc():
                    warnings.warn('You do not have a valid netrc file.  Setting access to public!', BrainUserWarning)
                    value = 'public'
            self._access = value
        else:
            raise ValueError('config.access must be one of {0}.'.format(self._access_types))

    @property
    def has_netrc(self):
        return self._check_netrc()

    def _load_defaults(self):
        ''' Load the Brain config yaml file '''

        config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'data/brain.yml')), Loader=get_yaml_loader())
        user_config_path = os.path.expanduser('~/.brain/brain.yml')
        if os.path.exists(user_config_path):
            config = merge(yaml.load(open(user_config_path), Loader=get_yaml_loader()), config)

        # update any matching Config values
        for key, value in config.items():
            if hasattr(self, key):
                self.__setattr__(key, value)

        self._custom_config = config

    def _check_paths(self):
        ''' Check the paths in the custom config '''

        if 'netrc_path' in self._custom_config:
            self._netrc_path = os.path.expanduser(self._custom_config['netrc_path'])
        htpass_path = self._custom_config.get('htpass_path', None)
        if htpass_path:
            self._htpass_path = htpass_path

    def _set_api_urls(self):
        ''' Set the API urls for production or test servers '''

        # check for
        use_test = self._custom_config.get('use_test', None)
        if use_test:
            self._public_api_url = 'https://lore.sdss.utah.edu/public/'
            self._collab_api_url = 'https://lore.sdss.utah.edu/test/'
        else:
            self._public_api_url = 'https://dr15.sdss.org/'
            self._collab_api_url = 'https://sas.sdss.org/'
            self._mirror_api_url = 'https://magrathea.sdss.org/'

        self.sasurl = os.getenv('SAS_URL') if 'SAS_URL' in os.environ else self._collab_api_url

    def _check_host(self, host, netfile, msg=None):
        ''' Check for a valid host in the netrc '''

        if host in netfile.hosts:
            self._valid_hosts[host] = True
        else:
            self._valid_hosts[host] = False
            basemsg = '{0} not found in netrc. '.format(host)
            if not msg:
                msg = ('{0} You will not have access '
                       'to SDSS data from {1}'.format(basemsg, host))
            else:
                msg = basemsg + msg

            warnings.warn(msg, BrainUserWarning)

    def _check_all_hosts(self, netfile=None):
        ''' Check all the hosts in the netrc file '''

        if not netfile:
            netfile = netrc.netrc(self._netrc_path)

        for host in self.hosts:
            self._check_host(host, netfile)

        # validate if any are good
        return any(self._valid_hosts.values())

    def _check_netrc(self):
        """Makes sure there is a valid netrc."""

        if not os.path.exists(self._netrc_path):
            raise BrainError('No .netrc file found in your HOME directory!')
        else:
            if oct(os.stat(self._netrc_path).st_mode)[-3:] != '600':
                raise BrainError('your .netrc file does not have 600 permissions. Please fix it by '
                                 'running chmod 600 ~/.netrc. Authentication will not work with '
                                 'permissions different from 600.')

            # read the netrc file
            netfile = netrc.netrc(self._netrc_path)

            # check the hosts
            self._check_host('data.sdss.org', netfile, msg='You will not be able to download SDSS data')
            self._check_host('api.sdss.org', netfile, msg='You will not have remote access to SDSS data')

            # validate if any are good
            return any(self._valid_hosts.values())

    def _read_netrc(self, host):
        ''' Read the netrc file for a given host '''

        if not self._check_netrc():
            raise BrainError('netrc did not pass checks.  Cannot read!')

        assert host in self._valid_hosts and self._valid_hosts[host], '{0} must be a valid host in the netrc'.format(host)

        netfile = netrc.netrc(self._netrc_path)
        user, acct, passwd = netfile.authenticators(host)
        return user, passwd


bconfig = BrainConfig()
