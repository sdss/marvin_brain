import json
from brain.api.base import BrainBaseView


class BrainQueryView(BrainBaseView):
    """Class describing API calls related to queries."""

    route_base = '/query/'

    def index(self):
        self.results['data'] = 'this is a query!'
        return json.dumps(self.results)

