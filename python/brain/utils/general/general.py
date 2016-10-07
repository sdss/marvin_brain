import numpy as np
import os
import decimal
import datetime

# General utilities

__all__ = []


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

    # Set the dbconfig variable
    if localhost:
        return 'local'
    elif utah or sasvm:
        return 'utah'
    else:
        return None


def convertIvarToErr(ivar):
    ''' Converts a list of inverse variance into an a list of standard errors '''

    assert type(ivar) == list or type(ivar) == np.ndarray, \
        'Input ivar is not of type list or an Numpy ndarray'

    if type(ivar) == list:
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
