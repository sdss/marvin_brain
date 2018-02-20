import os
import decimal
import datetime
import numpy as np
import json
from brain import bconfig
from brain.core.exceptions import BrainError, BrainWarning


# General utilities

__all__ = ['getDbMachine', 'convertIvarToErr', 'compress_data', 'uncompress_data']


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

    # Check if jhu or not
    jhu = 'jhu' in machine if machine else None

    # Set the dbconfig variable
    if localhost:
        return 'local'
    elif utah or sasvm:
        return 'utah'
    elif jhu:
        return 'jhu'
    else:
        return None


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
