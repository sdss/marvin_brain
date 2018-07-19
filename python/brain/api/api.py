from __future__ import print_function
import requests
from brain.core.exceptions import BrainError, BrainApiAuthError, BrainNotImplemented
from brain import bconfig
from brain.utils.general import uncompress_data
from brain.core.core import URLMapDict
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin
try:
    from cachecontrol import CacheControl as cache
except ImportError:
    cache = None

configkeys = []


class BrainInteraction(object):
    """ This class defines convenience wrappers for the Brain RESTful API """

    def __init__(self, route, params=None, request_type='post', auth='token',
                 timeout=(3.05, 300), headers=None, stream=None, datastream=None):
        self.results = None
        self.response_time = None
        self.route = route
        self.params = params
        self.request_type = request_type
        self.timeout = timeout
        self.stream = stream
        self.datastream = datastream
        self.headers = headers if headers is not None else {}
        self.statuscodes = {200: 'Ok', 401: 'Authentication Required', 404: 'URL Not Found',
                            500: 'Internal Server Error', 405: 'Method Not Allowed',
                            400: 'Bad Request', 502: 'Bad Gateway', 504: 'Gateway Timeout',
                            422: 'Unprocessable Entity', 429: 'Rate Limit Exceeded'}
        self.compression = self.params['compression'] if self.params and \
            'compression' in self.params else bconfig.compression

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

        # check access and authentication
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
        elif authtype == 'token':
            assert bconfig.token is not None, 'You must have a valid token set to use the API.  Please login.'
            self.headers.update({'Authorization': 'Bearer {0}'.format(bconfig.token)})

    def _decode_stream(self, content):
        ''' Decode the content string for a data stream

        Uncompresses the response content either using JSON or msgpack.
        Will uncompress the entire response content in single go. If
        datastream is True, then the content is streamed back using a
        generator and has been compressed row-by-row. See the generator
        query fxn in marvin/api/query.py.

        Parameters:
            content (str):
                The response content string

        Returns:
            The uncompressed content data

        '''

        if self.datastream:
            # since content is a single string, must split on the row separator
            data = [uncompress_data(row, uncompress_with=self.compression) for row in content.split(';\n') if row]
            # data is expected to be in a dictionary key called 'data'
            out = {}
            out['data'] = data
        else:
            out = uncompress_data(content, uncompress_with=self.compression)
        return out

    def _get_json(self, response):
        ''' Try to extract any json data

        Tries to use the built in json fxn to extract
        the response content

        Parameters:
            response:
                The full response

        Returns:
            The JSON data
        '''
        try:
            json = response.json()
        except ValueError as e:
            json = None
        return json

    def _get_data(self, response, chunksize=None, dtype=None):
        ''' Get json/binary data from the response content

        Tries to extract the data from the response content.
        If stream is set, then streams the response content in chunks and extracts
        the data, to save on client memory.  Otherwise reads the entire response
        content into memory at once.

        Parameters:
            response:
                The full response
            chunksize (int):
                The unit of the chunk size in bytes.  When None, chunksize determined by
                interal magic. Default is None
            dtype (str):
                The data type.  Either json or other (e.g. binary content using msgpack).

        Returns:
            The uncompressed data as a list.

        '''

        if self.stream:
            resstring = ''.join([bytes.decode(chunk) for chunk in response.iter_content(chunk_size=chunksize)])
            data = self._decode_stream(resstring)
        else:
            if dtype == 'json':
                data = self._get_json(response)
            else:
                data = uncompress_data(response.content, uncompress_with='msgpack')
        return data

    def _get_content(self, response):
        ''' Get the response content

        Gets the response content either as a JSON
        or binary data from msgpack

        Parameters:
            response:
                The full response

        Returns:
            The uncompressed data

        '''

        content_type = response.headers['Content-Type']
        if 'json' in content_type:
            data = self._get_data(response, dtype='json')
        elif 'octet-stream' in content_type:
            data = self._get_data(response)
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
                elif self.authtype == 'token':
                    msg = '{0}. Please check your token or login again for a fresh one.'.format(json_data['msg'])
                else:
                    msg = 'Please check your authentication method.'
                errmsg = json_data['error'] if 'error' in json_data else ''
                self._closeRequestSession()
                raise BrainApiAuthError('API Authentication Error: {0}. {1}'.format(msg, errmsg))
            elif self.status_code == 422:
                self._closeRequestSession()
                raise BrainError('Requests Http Status Error: {0}\nValidation Errors:\n{1}'.format(http, json_data))
            else:
                self._closeRequestSession()
                if 'api_error' in json_data:
                    apijson = json_data['api_error']
                    errmsg = '{0}\n{1}'.format(apijson['message'], apijson['traceback']) if 'message' in apijson else '{0}'.format(apijson['traceback'])
                elif 'error' in json_data:
                    err = json_data['error']
                    errmsg = '{0}'.format(err)
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
