##########################################################################
# ADOBE CONFIDENTIAL
#
# Copyright 2023 Adobe
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
The ``async_utils`` module provide primitives used in async computations.
"""

import dataclasses
import _substance_painter.async_utils


@dataclasses.dataclass(frozen=True)
class StopSource:
    """
    An object that can be used to cancel an asynchronous computation.
    """

    stop_source: _substance_painter.async_utils.StopSource

    def __bool__(self):
        return self.stop_source and self.stop_source.stop_possible()

    def request_stop(self) -> bool:
        """
        Makes a top request.

        Returns:
            bool: True if the stop request was possible.
        """
        return self.stop_source.request_stop()

    def stop_requested(self) -> bool:
        """
        Check if a stop request as been made.

        Returns:
            bool: True if a stop request has been made.
        """
        return self.stop_source.stop_requested()
