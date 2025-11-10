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
The ``substance_painter`` package is a collection of modules that give access
to `Substance 3D Painter` functions and runtime data.

You can for example:

    - Open, save, rename, etc. a `Substance 3D Painter` project with the
      :mod:`project` module.
    - Change the "Display Settings" or your project, like environment map and
      color grading, with the :mod:`display` module.
    - Change the channels of the Texture Set of your project with the
      :mod:`textureset` module.
    - Export the textures of your project with the :mod:`export` module.
    - Print messages to the console and the log file with the :mod:`logging`
      module.
    - Cutomize the UI of `Substance 3D Painter` with the :mod:`ui` module.

Event handling is done via the :mod:`event` module. Finally, the `Substance
Painter` Python API introduces several custom exceptions, which are listed and
documented in the :mod:`exception` module.
"""

__author__ = "Adobe"

from substance_painter import (
    application, async_utils, baking, colormanagement, display, event, exception,
    export, js, layerstack, levels, logging, project, properties, resource,
    source, textureset, ui)

# The version information is defined in a standalone file.
from ._version import (__version__, __version_info__)
