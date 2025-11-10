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
This module declares `Substance 3D Painter` specific exceptions.
"""

import _substance_painter.exception
from . import _utility

ProjectError = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.exception.ProjectError, __name__)
"""
Raised when an operation or function is incompatible with the current
project, or when the current state of the project is invalid.

Trying to save a project when there is no project opened would raise a
:class:`ProjectError`.
"""

ServiceNotFoundError = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.exception.ServiceNotFoundError, __name__)
"""
Raised when an operation or function relies on a service which could not
be found. It could mean that the service has not been started yet.

Trying to execute a command while Substance 3D Painter is starting could
raise :class:`ServiceNotFoundError`.
"""

ResourceNotFoundError = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.exception.ResourceNotFoundError, __name__)
"""
Raised when a Substance 3D Painter resource could not be found.

Providing an invalid resource ID would raise a :class:`ResourceNotFoundError`.
"""
