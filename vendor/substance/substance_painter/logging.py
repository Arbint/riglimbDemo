##########################################################################
# ADOBE CONFIDENTIAL
#
# Copyright 2020 Adobe
# All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of Adobe and its suppliers, if any. The intellectual
# and technical concepts contained herein are proprietary to Adobe
# and its suppliers and are protected by all applicable intellectual
# property laws, including trade secret and copyright laws.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Adobe.
##########################################################################

"""
This module exposes several functions to output messages to the `Substance
Painter` logger. Depending on the severity of the message, use :func:`info()`,
:func:`warning()` or :func:`error()`.

For a finer control over the logging parameters, namely severity and channel,
use :func:`log()`. The functions :func:`info()`, :func:`warning()` and
:func:`error()` will output to the `'Python'` log channel, while :func:`log()`
allows to specify a different channel.

Messages with severity levels ``INFO``, ``WARNING`` and ``ERROR`` are meant for
the end user, and will appear in the log window of `Substance 3D Painter`. Messages
with severity levels ``DBG_INFO``, ``DBG_WARNING`` and ``DBG_ERROR`` are meant
for the developer, and will appear in the log file.

Example:
    ::

        import substance_painter.logging

        # Simple log functions:
        substance_painter.logging.info("Everyone knows that 2 + 2 is {0}.".format(2+2))
        substance_painter.logging.warning("Maybe the user should look at this.")
        substance_painter.logging.error("Letting the user know that something went wrong.")

        # Log function with more options:
        substance_painter.logging.log(
            substance_painter.logging.INFO,
            "Python",
            "An informative log message to the 'Python' channel.")

        substance_painter.logging.log(
            substance_painter.logging.ERROR,
            "MyPlugin",
            "An error log message to the 'MyPlugin' channel.")
"""

# import explicitely everthing that is used from _substance_painter to avoid pylint errors
from _substance_painter.logging import PYTHON_CHANNEL
from _substance_painter.logging import LogSeverity as _LogSeverity
from _substance_painter.logging import log as _log

# Expose log severities to the public interface
INFO = _LogSeverity.INFO
WARNING = _LogSeverity.WARNING
ERROR = _LogSeverity.ERROR
DBG_INFO = _LogSeverity.DBG_INFO
DBG_WARNING = _LogSeverity.DBG_WARNING
DBG_ERROR = _LogSeverity.DBG_ERROR


def log(severity, channel: str, message: str):
    """Logs a message with level `severity` on the Substance 3D Painter logger.

    Args:
      severity: the severity level, can be ``INFO``, ``WARNING`` or ``ERROR`` for
          messages relevant to the end user, or ``DBG_INFO``, ``DBG_WARNING`` or
          ``DBG_ERROR`` for messages relevant to the developer.
      channel (str): the channel to log into.  This can be any name allowing to
                     identify the origin of the message, for example the name of
                     your plugin.
      message (str): the message to log.
    """
    _log(severity, channel, message)


# Add a few helpers:
def info(message: str):
    """Logs a message with level ``INFO`` on the Substance 3D Painter logger.

    Args:
        message (str): The message to log.
    """
    log(INFO, PYTHON_CHANNEL, message)


def warning(message: str):
    """Logs a message with level ``WARNING`` on the Substance 3D Painter logger.

    Args:
        message (str): The warning message to log.
    """
    log(WARNING, PYTHON_CHANNEL, message)


def error(message: str):
    """Logs a message with level ``ERROR`` on the Substance 3D Painter logger.

    Args:
        message (str): The error message to log.
    """
    log(ERROR, PYTHON_CHANNEL, message)
