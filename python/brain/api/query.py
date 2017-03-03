import json
from brain.api.base import BrainBaseView
from flask import jsonify


class BrainQueryView(BrainBaseView):
    """Class describing API calls related to queries."""

    route_base = '/query/'

    def index(self):
        self.results['data'] = 'this is a query!'
        return jsonify(self.results)

