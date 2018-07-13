# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This module defines a logging class based on the built-in logging module.
The module is heavily based on the astropy logging system.
"""

from __future__ import print_function

import logging
import os
import re
import shutil
import sys
import warnings
from logging import FileHandler
from logging.handlers import TimedRotatingFileHandler
from textwrap import TextWrapper

from brain.core.colourPrint import colourPrint
from brain.core.exceptions import BrainError, BrainWarning


# Initialize by calling initLog()
log = None

# Adds custom log level for important messages
IMPORTANT = 25
logging.addLevelName(IMPORTANT, 'IMPORTANT')

ansi_escape = re.compile(r'\x1b[^m]*m')


def important(self, message, *args, **kws):
    self._log(IMPORTANT, message, args, **kws)


logging.Logger.important = important


def initLog(logFilePath, logLevel='INFO', logFileLevel='DEBUG',
            mode='append', wrapperLength=80):

    logging.setLoggerClass(BrainLogger)
    log = logging.getLogger('Brain')
    log._set_defaults(logLevel=logLevel, logFileLevel=logFileLevel, logFilePath=logFilePath,
                      mode=mode, wrapperLength=wrapperLength)

    return log


class MyFormatter(logging.Formatter):

    warning_fmp = '%(asctime)s - %(levelname)s: %(message)s [%(origin)s]'
    info_fmt = '%(asctime)s - %(levelname)s - %(message)s [%(funcName)s @ ' + \
        '%(filename)s]'

    def __init__(self, fmt='%(levelname)s - %(message)s [%(funcName)s @ ' +
                 '%(filename)s]'):
        logging.Formatter.__init__(self, fmt, datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.INFO:
            self._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._fmt = MyFormatter.info_fmt

        elif record.levelno == logging.WARNING:
            self._fmt = MyFormatter.warning_fmp

        elif record.levelno == IMPORTANT:
            self._fmt = MyFormatter.info_fmt

        record.msg = ansi_escape.sub('', record.msg)

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


Logger = logging.getLoggerClass()
fmt = MyFormatter()


class BrainLogger(Logger):
    """This class is used to set up the logging system.

    The main functionality added by this class over the built-in
    logging.Logger class is the ability to keep track of the origin of the
    messages, the ability to enable logging of warnings.warn calls and
    exceptions, and the addition of colorized output and context managers to
    easily capture messages to a file or list.

    """

    def saveLog(self, path):
        shutil.copyfile(self.logFilename, os.path.expanduser(path))

    def _warn(self, *args, **kwargs):
        """Overrides `warnings.warn`

        Before calling the original `warnings.warn` function it makes sure
        the warning is redirected to the correct ``showwarning`` function.

        """

        if issubclass(kwargs['category'], BrainWarning):
            self._show_warning(*args, **kwargs)
        else:
            warnings._showwarning_orig(*args, **kwargs)

    def _show_warning(self, *args, **kwargs):

        warning = args[0]

        message = '{0}: {1}'.format(warning.__class__.__name__, args[0])
        mod_path = args[2]

        mod_name = None
        mod_path, __ = os.path.splitext(mod_path)
        for __, mod in sys.modules.items():
            mod_file = getattr(mod, '__file__', '')
            if mod_file is not None:
                path = os.path.splitext(mod_file)[0]
                if path == mod_path:
                    mod_name = mod.__name__
                    break

        if mod_name is not None:
            self.warning(message, extra={'origin': mod_name})
        else:
            self.warning(message, extra={'origin': 'no_module'})

    def warning(self, message, *args, **kwargs):

        # if there are args then we have old style formating
        if args:
            message = message % args

        # check for the extra keyword in kwargs
        extra = kwargs.get('extra', None)
        if extra is None:
            extra = {'origin': ''}

        super(BrainLogger, self).warning(message, extra=extra)

    def _stream_formatter(self, record):
        """The formatter for standard output."""
        if record.levelno < logging.DEBUG:
            print(record.levelname, end='')
        elif(record.levelno < logging.INFO):
            colourPrint(record.levelname, 'green', end='')
        elif(record.levelno < IMPORTANT):
            colourPrint(record.levelname, 'magenta', end='')
        elif(record.levelno < logging.WARNING):
            colourPrint(record.levelname, 'lightblue', end='')
        elif(record.levelno < logging.ERROR):
            colourPrint(record.levelname, 'brown', end='')
        else:
            colourPrint(record.levelname, 'red', end='')

        if record.levelno == logging.WARN:
            message = '{0}'.format(record.msg[record.msg.find(':') + 2:])
        else:
            message = '{0}'.format(record.msg)

        if len(message) > self.wrapperLength:
            tw = TextWrapper()
            tw.width = self.wrapperLength
            tw.subsequent_indent = ' ' * (len(record.levelname) + 2)
            tw.break_on_hyphens = False
            message = '\n'.join(tw.wrap(message))

        print(': ' + message)

    def _set_defaults(self,
                      logLevel='WARNING',
                      logFileLevel='INFO',
                      logFilePath='~/.brain/brain.log',
                      mode='append',
                      wrapperLength=70):
        """Reset logger to its initial state."""

        # Remove all previous handlers
        for handler in self.handlers[:]:
            self.removeHandler(handler)

        # Set levels
        self.setLevel('DEBUG')

        # Set up the stdout handler
        self.sh = logging.StreamHandler()
        self.sh.emit = self._stream_formatter
        self.addHandler(self.sh)

        self.wrapperLength = wrapperLength

        # Set up the main log file handler if requested (but this might fail if
        # configuration directory or log file is not writeable).

        logFilePath = os.path.expanduser(logFilePath)
        logDir = os.path.dirname(logFilePath)
        if not os.path.exists(logDir):
            os.mkdir(logDir)

        try:
            if mode.lower() == 'overwrite':
                self.fh = FileHandler(logFilePath, mode='w')
            elif mode.lower() == 'append':
                self.fh = TimedRotatingFileHandler(
                    logFilePath, when='midnight', utc=True)
            else:
                raise BrainError('logger mode {0} not recognised'.format(mode))
        except (IOError, OSError) as e:
            warnings.warn(
                'log file {0!r} could not be opened for writing: '
                '{1}'.format(logFilePath, unicode(e)), RuntimeWarning)
        else:
            self.fh.setFormatter(fmt)
            self.addHandler(self.fh)

        # Adds a header only to the file handler
        self.sh.setLevel(logging.CRITICAL)
        self.fh.setLevel(logging.DEBUG)
        self.debug('')
        self.debug('--------------------------------')
        self.debug('----- Restarting logger. -------')
        self.debug('--------------------------------')

        self.sh.setLevel(logLevel)
        self.fh.setLevel(logFileLevel)

        self.logFilename = logFilePath
