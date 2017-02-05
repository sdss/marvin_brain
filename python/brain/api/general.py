#!/usr/bin/env python
# encoding: utf-8
"""

general.py

Licensed under a 3-clause BSD license.

Revision history:
    17 Feb 2016 J. Sánchez-Gallego
      Initial version
    18 Feb 2016 B. Cherinka
        Added buildRouteMap API call

"""

from __future__ import division
from __future__ import print_function
from flask_classy import route
from brain.api.base import BrainBaseView
from brain.core.exceptions import BrainError
from flask import url_for, current_app, jsonify
import json
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote


class BrainGeneralRequestsView(BrainBaseView):
    """A collection of requests for generic purposes."""

    route_base = '/general/'

    def index(self):
        res = {'data': 'this is a general Brain Function!'}
        self.update_results(res)
        return jsonify(self.results)

    @route('/getroutemap/', endpoint='getroutemap')
    def buildRouteMap(self):
        """ Build the URL route map for all routes in the Flask app.

        .. :quickref: General; Returns the urlmap dictionary of Marvin API routes

        Syntax of output:  {"api": {blueprint: {endpoint: {'methods':x, 'url':x} } }

        :form release: the release of MaNGA
        :resjson int status: status of response. 1 if good, -1 if bad.
        :resjson string error: error message, null if None
        :resjson json inconfig: json of incoming configuration
        :resjson json utahconfig: json of outcoming configuration
        :resjson string traceback: traceback of an error, null if None
        :resjson json data: dictionary of returned data
        :json dict urlmap: dict of the Marvin API routes
        :resheader Content-Type: application/json
        :statuscode 200: no error
        :statuscode 422: invalid input parameters
        :raises BrainError: Raised when url_for can't format the endpoint name into a valid url.

        **Example request**:

        .. sourcecode:: http

           GET /marvin2/api/general/getroutemap/ HTTP/1.1
           Host: api.sdss.org
           Accept: application/json, */*

        **Example response**:

        .. sourcecode:: http

           HTTP/1.1 200 OK
           Content-Type: application/json
           {
              "status": 1,
              "error": null,
              "inconfig": {"release": "MPL-5"},
              "utahconfig": {"release": "MPL-5", "mode": "local"},
              "traceback": null,
              "data": {"urlmap": {"api": {"CubeView:index": {"methods": "HEAD,OPTIONS,GET","url": "/marvin2/api/cubes/"},
                                         ...
                                 }
                      }
           }

        """

        output = {}
        for rule in current_app.url_map.iter_rules():
            # get options
            options = {}
            for arg in rule.arguments:
                options[arg] = '[{0}]'.format(arg)
            options['_external'] = False
            # get endpoint
            fullendpoint = rule.endpoint
            esplit = fullendpoint.split('.')
            grp, endpoint = esplit[0], None if len(esplit) == 1 else esplit[1]
            output.setdefault(grp, {}).update({endpoint: {}})
            # get methods
            methods = ','.join(rule.methods)
            output[grp][endpoint]['methods'] = methods
            # build url
            try:
                rawurl = url_for(fullendpoint, **options)
            except ValueError as e:
                raise BrainError('Error generating url for {0}: {1}'.format(fullendpoint, e))
            url = unquote(rawurl).replace('[', '{').replace(']', '}')
            output[grp][endpoint]['url'] = url

        res = {'urlmap': output, 'status': 1}
        self.update_results(res)
        return jsonify(self.results)


# GeneralRequestsView.register(apiGeneral)
