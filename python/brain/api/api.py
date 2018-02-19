from __future__ import print_function
import os
import requests
import json
import msgpack
import msgpack_numpy as m
from brain.core.exceptions import BrainError, BrainApiAuthError, BrainNotImplemented
from brain import bconfig
from brain.core.core import URLMapDict
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
try:
    from cachecontrol import CacheControl as cache
except ImportError:
    cache = None

m.patch()
configkeys = []


class BrainInteraction(object):
    """ This class defines convenience wrappers for the Brain RESTful API """

    def __init__(self, route, params=None, request_type='post', auth='netrc',
                 timeout=(3.05, 300), headers=None, stream=None):
        self.results = None
        self.response_time = None
        self.route = route
        self.params = params
        self.request_type = request_type
        self.timeout = timeout
        self.stream = stream
        self.headers = headers if headers is not None else {}
        self.statuscodes = {200: 'Ok', 401: 'Authentication Required', 404: 'URL Not Found',
                            500: 'Internal Server Error', 405: 'Method Not Allowed',
                            400: 'Bad Request', 502: 'Bad Gateway', 504: 'Gateway Timeout',
                            422: 'Unprocessable Entity', 429: 'Rate Limit Exceeded'}

        self.url = urljoin(bconfig.sasurl, route) if self.route else None

        # set request Session
        self._setRequestSession()

        # set authentication
        self.setAuth(authtype=auth)

        # sends the request
        if self.url:
            self._sendRequest(request_type)
        else:
            raise BrainError('No route and/or url specified {0}'.format(self.url))

    def __repr__(self):
        return ('Interaction(route={0}, params={1}, request_type={2})'
                .format(self.route, repr(self.params), self.request_type))

    def _setRequestSession(self):
        ''' creates or sets the Brain requests Session object '''
        if isinstance(bconfig.request_session, type(None)):
            if not cache:
                bconfig.request_session = requests.Session()
            else:
                bconfig.request_session = cache(requests.Session())
            self.session = bconfig.request_session
        else:
            self.session = bconfig.request_session

    def _closeRequestSession(self):
        ''' closes the Brain requests Session object'''
        self.session.close()
        bconfig.request_session.close()
        bconfig.request_session = None

    def setAuth(self, authtype='netrc'):
        ''' set the session authentication '''
        self.authtype = authtype
        if authtype == 'netrc':
            # do nothing since this is default with no auth set
            pass
        elif authtype == 'http':
            from requests_toolbelt import GuessAuth
            auth = GuessAuth('user', 'passwd')
            self.session.auth = auth
        elif authtype == 'oauth':
            raise BrainNotImplemented('OAuth authentication')

    def _get_json(self, response):
        ''' Try to extract any json data '''
        try:
            json = response.json()
        except ValueError as e:
            json = None
        return json

    def _get_json_data(self, response, chunksize=None):
        ''' Try to extract json data from a stream or using json() '''

        if self.stream:
            resstring = ''.join([chunk for chunk in response.iter_content(chunk_size=chunksize)])
            json_data = json.loads(resstring.decode())
        else:
            json_data = self._get_json(response)

        return json_data

    def _get_binary_data(self, response, chunksize=None):
        ''' Get binary data from msgpack '''

        if self.stream:
            resstring = ''.join([chunk for chunk in response.iter_content(chunk_size=chunksize)])
            unpacked = msgpack.unpackb(resstring, raw=False)
        else:
            unpacked = msgpack.unpackb(response.content, raw=False)
        return unpacked

    def _get_content(self, response):
        ''' Get the response content '''

        content_type = response.headers['Content-Type']
        if 'json' in content_type:
            data = self._get_json_data(response)
        elif 'octet-stream' in content_type:
            data = self._get_binary_data(response)
        else:
            data = response.content

        return data

    def _checkResponse(self, response):
        ''' Checks the response for proper http status code '''

        # check for bad status
        try:
            isbad = response.raise_for_status()
        except requests.HTTPError as http:
            self.status_code = response.status_code
            errmsg = 'Error accessing {0}: {1}-{2}'.format(response.url, response.status_code,
                                                           self.statuscodes[response.status_code])
            self.results = {'http_status_code': response.status_code, 'message': errmsg}
            json_data = self._get_content(response)
            if self.status_code == 401:
                if self.authtype == 'netrc':
                    msg = 'Please create or check credentials in your local .netrc file'
                elif self.authtype == 'oauth':
                    msg = 'Please check your Oauth authentication'
                elif self.authtype == 'http':
                    msg = 'Please check your http/digest authentication'
                self._closeRequestSession()
                raise BrainApiAuthError('API Authentication Error: {0}'.format(msg))
            elif self.status_code == 422:
                self._closeRequestSession()
                raise BrainError('Requests Http Status Error: {0}\nValidation Errors:\n{1}'.format(http, json_data))
            else:
                self._closeRequestSession()
                apijson = json_data['api_error']
                errmsg = '{0}\n{1}'.format(apijson['message'], apijson['traceback']) if 'message' in apijson else '{0}'.format(apijson['traceback'])
                raise BrainError('Requests Http Status Error: {0}\n{1}'.format(http, errmsg))
        else:
            # Not bad
            assert isbad is None, 'Http status code should not be bad'
            assert response.ok is True, 'Ok status should be true'

            # if 'route' not in self.url and 'clean' not in self.url:
            #     self._closeRequestSession()
            #     raise BrainError('test error is now raised here')

            self.status_code = response.status_code
            self.results = self._get_content(response)
            self.response_time = response.elapsed
            if not self.results:
                self.results = response.text
                self._closeRequestSession()
                raise BrainError('Response not in JSON format. {0}'.format(self.results))

            # Raises an error if status is -1
            if 'status' in self.results and self.results['status'] == -1:
                errorMsg = 'no error message provided' \
                    if 'error' not in self.results else self.results['error']
                self._check_for_traceback()
                self._closeRequestSession()
                raise BrainError('Something went wrong on the server side: {0}'.format(errorMsg))

    def _check_for_traceback(self):
        ''' checks the response for a traceback in the results response '''
        bconfig.traceback = self.results.get('traceback', None)

    def _sendRequest(self, request_type):
        ''' sends the api requests to the server '''
        assert request_type in ['get', 'post'], 'Valid request types are "get" and "post".'

        # Loads the local config parameters
        self._loadConfigParams()
        # Send the request
        try:
            if request_type == 'get':
                self._response = self.session.get(self.url, params=self.params, timeout=self.timeout,
                                                  headers=self.headers, stream=self.stream)
            elif request_type == 'post':
                self._response = self.session.post(self.url, data=self.params, timeout=self.timeout,
                                                   headers=self.headers, stream=self.stream)
        except requests.Timeout as rt:
            self._closeRequestSession()
            errmsg = 'Your request took longer than 5 minutes and timed out. Please try again or simplify your request.'
            raise BrainError('Requests Timeout Error: {0}\n{1}'.format(rt, errmsg))
        except requests.URLRequired as urlreq:
            self._closeRequestSession()
            raise BrainError('Requests Valid URL Required: {0}'.format(urlreq))
        except requests.ConnectionError as con:
            self._closeRequestSession()
            raise BrainError('Requests Connection Error: {0}'.format(con))
        except requests.RequestException as req:
            self._closeRequestSession()
            raise BrainError('Ambiguous Requests Error: {0}'.format(req))
        else:
            # Check the response if it's good
            self._checkResponse(self._response)

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
        self.params.update({'session_id': bconfig.session_id})

    def getRouteMap(self):
        """Retrieve the URL routing map if it exists."""

        if 'urlmap' in self.results:
            return URLMapDict(self.results['urlmap'])
        else:
            return URLMapDict()
