#!/usr/bin/env python
# encoding: utf-8

"""
Licensed under a 3-clause BSD license.

Revision History:
    Initial Version: 2016-02-17 17:46:57
    Last Modified On: 2016-02-17 17:46:57 by Brian

"""
from __future__ import print_function
from __future__ import division
from flask_classful import FlaskView
from flask import request, current_app, jsonify
from brain import bconfig
from brain.core.exceptions import BrainError


def processRequest(request=None, as_dict=None, param=None):
    '''Generally process the request for POST or GET, and build a form dict

        Parameters:
            request (request):
                HTTP request object containing POST or GET data
            as_dict (bool):
                Boolean indicating whether to return the data as a standard dict or not
        Returns:
            Dict or ImmutableMultiDict
    '''

    # get form data
    if request.method == 'POST':
        if not request.form:
            # if data is content-type json
            data = request.get_json()
        else:
            # if data is content-type form
            data = request.form
    elif request.method == 'GET':
        data = request.args
    else:
        return {}

    # # if no data at all, return nothing
    if param and data:
        return data.get(param, None)

    # convert ImmutableMultiDict to dictionary (if get or post-form) or use dict if post-json
    if as_dict:
        if isinstance(data, dict):
            form = data
        else:
            # use multidict lists and iterlists to group multiple values for same in key into list
            try:
                # py2.7
                form = {key: val if len(val) > 1 else val[0] for key, val in data.iterlists()}
            except AttributeError:
                # py3.5
                form = {key: val if len(val) > 1 else val[0] for key, val in data.lists()}
    else:
        form = data

    return form


class BrainBaseView(FlaskView):
    """Super Class for all API Views to handle all global API items of interest"""

    def __init__(self):
        self.reset_results()
        bconfig.mode = 'local'

    def reset_results(self):
        self.results = {'data': None, 'status': -1, 'error': None, 'traceback': None}

    def update_results(self, newresults):
        self.results.update(newresults)

    def reset_status(self):
        self.results['status'] = -1

    def add_config(self):
        pass

    def before_request(self, *args, **kwargs):
        form = processRequest(request=request)
        self._release = form.get('release', None) if form else None
        self._endpoint = request.endpoint
        self.results['inconfig'] = form
        if form:
            for key, val in form.items():
                bconfig.__setattr__(key, val)
        # adds the out going config info into the results (placed here since didn't work in
        # after_request; obstensibly the in and out configs should match)
        self.add_config()

        # check API Authentication
        try:
            self._checkAuth()
        except BrainError as e:
            msg = 'Brain Authorization Error: {0}.  Check your token or netrc file'.format(e)
            return jsonify({'error': msg, 'status': -1})

    def after_request(self, name, response):
        """This performs a reset of the results dict after every request method runs.

        See Flask-Classy for more info on after_request."""

        self.reset_results()
        return response

    def _checkAuth(self):
        ''' Checks the API for authentication

        Main user and token authentication take care of in each request.
        See decorators applied to marvin.api.base
        '''

        # don't check authentication for these public decorated routes
        ispublic = getattr(current_app.view_functions[request.endpoint], 'is_public', False)
        if ispublic:
            return

        if 'Authorization' not in request.headers:
            raise BrainError('Authorization is required to access!')


