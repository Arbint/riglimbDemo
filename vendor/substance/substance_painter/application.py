##########################################################################
# ADOBE CONFIDENTIAL
#
# Copyright 2022 Adobe
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
This module contains application wide functionnalities.
"""

import contextlib
from typing import Tuple

import _substance_painter.feature
import _substance_painter.application


def version_info() -> Tuple[int, int, int]:
    """
    Get the version_info of Substance 3D Painter. Ie a tuple containing major, minor, patch.

    Returns:
        Tuple[int, int, int]: The major, minor and patch version of Substance 3D Painter.
    """
    return _substance_painter.feature.application_version()


def version() -> str:
    """
    Get the version of Substance 3D Painter. Do not extract version information out of it,
    rather use :func:`version_info`.

    Returns:
        str: Version of Substance 3D Painter.
    """
    return ".".join(str(n) for n in version_info())


def engine_computations_status() -> bool:
    """
    Check whether engine computations are enabled.

    Returns:
        bool: Whether engine computations are enabled.
    """
    return _substance_painter.feature.engine_computations_status()


def enable_engine_computations(enable: bool):
    """
    Enable or disable engine computations.
    """
    _substance_painter.feature.enable_engine_computations(enable)


@contextlib.contextmanager
def disable_engine_computations():
    """
    Context manager to disable engine computations.
    Allows to regroup computation intensive tasks without triggerring the engine so that textures
    are not computed or updated in the layer stack or the viewport.
    This is equivalent to disabling and then reenabling the engine by calling
    :func:`enable_engine_computations`.

    Example:
    ::

        import substance_painter.application as mapplication

        with mapplication.disable_engine_computations():
            # Do some computation intensive tasks
            pass
    """
    enable_engine_computations(False)
    yield
    enable_engine_computations(True)


def close():
    """
    Close Susbtance 3D Painter.

    Warning:
        Any unsaved data will be lost.
    """
    _substance_painter.application.close()
