import os
import decimal
import datetime
import numpy as np
import json
from brain.core.exceptions import BrainError, BrainWarning
from hashlib import md5
from passlib.apache import HtpasswdFile

from flask import url_for
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

# General utilities

__all__ = ['getDbMachine', 'merge', 'convertIvarToErr', 'compress_data',
           'uncompress_data', 'inspection_authenticate', 'validate_user',
           'get_db_user', 'build_routemap']


def getDbMachine():
    ''' Get the machine that the app is running on.

    This determines correct database and app configuration '''
    # Get machine
    machine = os.environ.get('HOSTNAME', None)

    # Check if localhost or not
    try:
        localhost = bool(os.environ['MANGA_LOCALHOST'])
    except:
        localhost = machine == 'manga'

    # Check if Utah or not
    try:
        utah = os.environ['UUFSCELL'] == 'kingspeak.peaks'
    except:
        utah = None
    # Check if sas-vm or not
    sasvm = 'sas-vm' in machine if machine else None

    # Check if lore or not
    lore = 'lore' in machine if machine else None

    # Check if jhu or not
    jhu = 'jhu' in machine if machine else None

    # Set the dbconfig variable
    if localhost:
        return 'local'
    elif utah or sasvm:
        return 'utah'
    elif lore:
        return 'lore'
    elif jhu:
        return 'jhu'
    else:
        return None


def merge(user, default):
    """Merges a user configuration with the default one.

    Merges two dictionaries, replacing default values
    of similar matching keys from user.

    Parameters:
        user (dict):
            A user defined dictionary
        default (dict):

    Returns:
        A new merged dictionary
    """

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge(user[kk], vv)

    return user


def convertIvarToErr(ivar):
    ''' Converts a list of inverse variance into an a list of standard errors '''

    assert isinstance(ivar, (list, np.ndarray)), 'Input ivar is not of type list or an Numpy ndarray'

    if isinstance(ivar, list):
        ivar = np.array(ivar)

    error = np.zeros(ivar.shape)
    notnull = ivar != 0.0
    error[notnull] = 1 / np.sqrt(ivar[notnull])
    error = list(error)
    return error


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)


def _compress_json(data, uncompress=None):
    ''' Compress/Uncompress JSON data '''

    try:
        if uncompress:
            comp_data = json.loads(data)
        else:
            comp_data = json.dumps(data)
    except Exception as e:
        raise BrainError('Cannot (un)compress JSON data. {0}'.format(e))
    else:
        return comp_data


def _compress_msgpack(data, uncompress=None):
    ''' Compress/Uncompress msgpack data '''

    # import the package
    try:
        import msgpack
        import msgpack_numpy as m
    except ImportError as e:
        compress_with = 'json'
        raise BrainWarning('Must have Python packages msgpack and msgpack_numpy '
                           'installed to use msgpack compression.  Defaulting to json')
    else:
        m.patch()

    # do the compression
    try:
        if uncompress:
            comp_data = msgpack.unpackb(data, raw=False)
        else:
            comp_data = msgpack.packb(data, use_bin_type=True)
    except Exception as e:
        raise BrainError('Cannot (un)compress msgpack data. {0}'.format(e))
    else:
        return comp_data


def compress_data(data, compress_with=None, uncompress=None):
    ''' Compress data via json or msgpack

    Parameters:
        data (obj)
            The input data to compress or uncompress
        compress_with (str):
            Compression algorithm.  Defaults to config.compression.
        uncompress (bool):
            If True, uncompresses the data instead of compressing.  Default is False

    Returns:
        Data compressed with with json or msgpack
    '''

    from brain import bconfig
    # check compression
    if not compress_with:
        compress_with = bconfig.compression
        if compress_with == 'msgpack':
            try:
                import msgpack
            except ImportError as e:
                compress_with = 'json'
                raise BrainWarning('Must have Python packages msgpack and msgpack_numpy '
                                   'installed to use msgpack compression.  Defaulting to json')

    assert compress_with in bconfig._compression_types, 'compress_with must be one of {0}'.format(bconfig._compression_types)

    # compress the data
    if compress_with == 'json':
        comp_data = _compress_json(data, uncompress=uncompress)
    elif compress_with == 'msgpack':
        comp_data = _compress_msgpack(data, uncompress=uncompress)
    else:
        raise BrainError('Unrecognized compression algorithm {0}'.format(compress_with))

    return comp_data


def uncompress_data(data, uncompress_with=None):
    ''' Compress data via json or msgpack

    Parameters:
        data (obj)
            The data to compress
        uncompress_with (str):
            Compression algorithm.  Defaults to config.compression.

    Returns:
        Data compressed with with json or msgpack
    '''

    return compress_data(data, compress_with=uncompress_with, uncompress=True)


def inspection_authenticate(session, username=None, password=None):
    ''' Authenticate with Trac using Inspection '''

    try:
        from inspection.marvin import Inspection
    except ImportError as e:
        from brain.core.inspection import Inspection

    auth = md5("{0}:AS3Trac:{1}".format(username, password).encode('utf-8')).hexdigest() if username and password else None
    result = {'is_valid': False}
    try:
        inspection = Inspection(session, username=username, auth=auth)
    except Exception as e:
        result['status'] = -1
        result['message'] = str(e)
    else:
        result = inspection.result()
        result['is_valid'] = inspection.ready
    return result


def validate_user(username, password, htpassfile=None, session={}, request=None):
    ''' Validate the User with htpassfile or Trac '''

    from brain import bconfig
    result = {}

    # validate the user with htpassfile or trac username
    is_valid = False
    user = None
    # try from request
    if not htpassfile and request:
        htpassfile = request.environ.get('HTPASSFILE', None)

    # try from brain config
    if not htpassfile and hasattr(bconfig, '_htpass_path'):
        htpassfile = bconfig._htpass_path

    # validate user
    if username == 'sdss':
        if htpassfile:
            htpass = HtpasswdFile(htpassfile)
            is_valid = htpass.check_password(username, password)
            user = username
        else:
            result['error'] = 'No valid htpasswd file found!'
    else:
        result = inspection_authenticate(session, username=username, password=password)
        is_valid = result['is_valid']
        user = result.get('membername', None)

    return is_valid, user, result


def get_db_user(username, password, dbsession=None, user_model=None, request=None):
    ''' Get a User from a database session '''

    if not dbsession:
        return None

    if user_model:
        assert hasattr(user_model, 'set_password'), 'User Model must have the set_password method!'
        assert hasattr(user_model, 'check_password'), 'User Model must have the check_password method!'

    user = dbsession.query(user_model).filter(user_model.username == username).one_or_none()
    with dbsession.begin():
        if not user:
            # add new user
            user = user_model(username=username, login_count=1)
            user.set_password(password)
            dbsession.add(user)
        else:
            user.update_stats(request=request)

    return user


def build_routemap(app):
    ''' Builds a Flask Web App's dictionary of routes

    Constructs a dictionary containing all the routes defined
    inside a given Flask Web App.  The route endpoints are deconstructed into
    a set of nested dictionaries of the form [blueprint][endpoint], which
    contains a methods and a url key.  The url key returns the full route path.

    E.g. the API route to get a cube, which has a name "getCube" is expressed as
    ['api']['getCube'].  To access the url, ['api']['getCube']['url'] returns
    "/marvin/api/cubes/{name}/"

    Parameters:
        app (Flask Application):
            The Flask app to extract routes from

    Returns:
        A dict of all routes
    '''

    output = {}
    for rule in app.url_map.iter_rules():
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

    return output

