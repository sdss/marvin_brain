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
from flask import url_for, current_app
import json
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote



# apiGeneral = Blueprint("apiGeneral", __name__)


class BrainGeneralRequestsView(BrainBaseView):
    """A collection of requests for generic purposes."""

    route_base = '/general/'

    def index(self):
        res = {'data': 'this is a general Brain Function!'}
        self.update_results(res)
        return json.dumps(self.results)

    @route('/getroutemap/', endpoint='getroutemap')
    def buildRouteMap(self):
        """ Build the URL route map for all routes in the Flask app.

        Returns in self.results a key 'urlmap' of dictionary of routes.

        Syntax:  {blueprint: {endpoint: {'methods':x, 'url':x} }

        E.g. getSpectrum method
        urlmap = {'api': {'getspectra': {'methods':['GET','POST'], 'url': '/api/cubes/{name}/spectra/{path}'} } }

        urls can now easily handle variable replacement in real code; MUST use
        keyword substitution. E.g.

        :status 400: when form parameters are missing
        :status 500: something goes wrong

        Raises:
            BrainError:
                Raised when url_for can't format the endpoint name into a valid url.

        Example:
            >>> print urlmap['api']['getspectra']['url'].format(name='1-209232',path='x=10/y=5')
            >>> '/api/cubes/1-209232/spectra/x=10/y=5'
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
        return json.dumps(self.results)


# GeneralRequestsView.register(apiGeneral)
