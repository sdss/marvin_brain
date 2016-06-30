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
from flask.ext.classy import FlaskView
from flask import request
from brain import bconfig


def processRequest(request=None, raw=None):
    '''Generally process the request for POST or GET, and build a form dict

        Parameters:
            request (request):
                HTTP request object containing POST or GET data
            raw (bool):
                Boolean indicating whether to return the raw request data or not
        Returns:
            Dict or ImmutableMultiDict
    '''

    # get form data
    if request.method == 'POST':
        data = request.form
    elif request.method == 'GET':
        data = request.args
    else:
        return None

    # Return Raw Request Data
    if raw:
        return data

    # build form dictionary
    try:
        form = {key: val if len(val) > 1 else val[0] for key, val in data.iterlists()}
    except AttributeError:
        form = {key: val if len(val) > 1 else val[0] for key, val in data.lists()}

    return form


class BrainBaseView(FlaskView):
    """Super Class for all API Views to handle all global API items of interest"""

    def __init__(self):
        self.reset_results()
        bconfig.mode = 'local'

    def reset_results(self):
        """Resets results to return from API as JSON."""
        self.results = {'data': None, 'status': -1, 'error': None}

    def update_results(self, newresults):
        """ Add to or Update the results dictionary """
        self.results.update(newresults)

    def reset_status(self):
        """ Resets the status to -1 """
        self.results['status'] = -1

    def add_config(self):
        pass

    def before_request(self, *args, **kwargs):
        form = processRequest(request=request)
        print('my form', form)
        self.results['inconfig'] = form
        for key, val in form.items():
            bconfig.__setattr__(key, val)
        # adds the out going config info into the results (placed here since didn't work in
        # after_request; obstensibly the in and out configs should match)
        self.add_config()

    def after_request(self, name, response):
        """This performs a reset of the results dict after every request method runs.

        See Flask-Classy for more info on after_request."""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')

        self.reset_results()
        return response

