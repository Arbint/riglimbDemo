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
The ``_executor`` module defines application specific executors.
"""

import collections
import traceback
import PySide6.QtCore
import _substance_painter.project
from . import event


class ProjectExecutor:  #pylint: disable=too-few-public-methods
    """
    Execute code at specific project dependant times.
    """

    def __init__(self, dispatcher):
        self._queue = collections.deque()
        self._in_callback = False
        dispatcher.connect(event.ProjectAboutToClose, self._on_project_about_to_close)

    def _enqueue(self, callback):
        self._queue.append(callback)
        if len(self._queue) == 1 and not self._in_callback:
            PySide6.QtCore.QTimer.singleShot(0, self._try_dequeue)

    def _try_dequeue(self):
        if not self._queue:
            # project must have been closed
            return
        if not _substance_painter.project.is_busy():
            callback = self._queue.popleft()
            self._execute(callback)
        else:  #retry later
            PySide6.QtCore.QTimer.singleShot(0, self._try_dequeue)

    def _execute(self, callback):
        self._in_callback = True
        try:
            callback()
        except:  #pylint: disable=bare-except
            traceback.print_exc()
        self._in_callback = False
        # continuation
        if self._queue:
            PySide6.QtCore.QTimer.singleShot(0, self._try_dequeue)

    def _on_project_about_to_close(self, _event):
        self._queue.clear()

    def execute_when_not_busy(self, callback):
        """
        Execute code when the application is not in a busy state.
        """
        if not self._queue and not _substance_painter.project.is_busy() and not self._in_callback:
            self._execute(callback)
            return
        self._enqueue(callback)


PROJECT_EXECUTOR = ProjectExecutor(event.DISPATCHER)
"""The ProjectExecutor instance."""
