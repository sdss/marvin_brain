from __future__ import print_function
import os
import requests
from brain.core.exceptions import BrainError
from brain import bconfig

configkeys = {}


class Interaction(object):
    """ This class defines convenience wrappers for the Marvin RESTful API """

    def __init__(self, route, params=None, request_type='post'):
        self.results = None
        self.route = route
        self.params = params
        self.request_type = request_type
        self.statuscodes = {200: 'Ok', 401: 'Authentication Required', 404: 'URL Not Found',
                            500: 'Internal Server Error', 405: 'Method Not Allowed',
                            400: 'Bad Request', 502: 'Bad Gateway', 504: 'Gateway Timeout'}

        # TODO - look into this url routing , slash either
        # self.url = os.path.join(config.sasurl, route) if self.route else None

        self.url = self.route if bconfig.sasurl in self.route \
            else os.path.join(bconfig.sasurl, route) if self.route else None

        if self.url:
            self._sendRequest(request_type)
        else:
            raise BrainError('No route and/or url specified {0}'.format(self.url))

    def __repr__(self):
        return ('Interaction(route={0}, params={1}, request_type={2})'
                .format(self.route, repr(self.params), self.request_type))

    def _checkResponse(self, response):
        if response.status_code == 200:
            self.status_code = 200
            try:
                self.results = response.json()
            except ValueError as e:
                self.results = response.text
                raise BrainError('Response not in JSON format. {0} {1}'.format(e, self.results))
        else:
            self.status_code = response.status_code
            errmsg = 'Error accessing {0}: {1}-{2}'.format(response.url, response.status_code,
                                                           self.statuscodes[response.status_code])
            self.results = {'http_status_code': response.status_code, 'message': errmsg}
            raise BrainError('Response Error: {0}'.format(errmsg))

    def _sendRequest(self, request_type):

        assert request_type in ['get', 'post'], 'Valid request types are "get" and "post".'

        # Loads the local config parameters
        self._loadConfigParams()
        # Send the request
        if request_type == 'get':
            r = requests.get(self.url, params=self.params)
        elif request_type == 'post':
            r = requests.post(self.url, data=self.params)
        # Check the response if it's good
        self._checkResponse(r)

    def getData(self, astype=None):
        data = self.results['data'] if 'data' in self.results else None

        if astype and data:
            try:
                return astype(data)
            except Exception as e:
                raise Exception('Failed: {0}, {1}'.format(e, data))
        else:
            return data

    # This should probably get moved into the server side code
    def _preloadResults(self):
        for key in configkeys:
            self.results[key] = bconfig.__getattribute__(key)

    def checkMyConfig(self):
        return {k: self.results[k] if k in self.results else '' for k in configkeys}

    def _loadConfigParams(self):
        """Load the local configuration into a parameters dictionary to be sent with the request"""
        if self.params:
            for k in configkeys:
                self.params[k] = bconfig.__getattribute__(k)
        else:
            self.params = {k: bconfig.__getattribute__(k) for k in configkeys}

    def getRouteMap(self):
        """Retrieve the URL routing map if it exists."""
        return self.results.get('urlmap', None)

    def getQuery(self):
        """Print SQL query."""
        pass