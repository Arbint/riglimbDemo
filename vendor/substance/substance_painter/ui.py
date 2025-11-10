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
Entry points to customize `Substance 3D Painter` UI.
"""

import shiboken6
import PySide6.QtCore
import PySide6.QtWidgets
import PySide6.QtGui
import _substance_painter.ui
from . import _utility

UIMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.ui.UIMode, __name__, [('Edition', 1)])
"""UI configurations enumeration.

Members:

================= ====== ===========================
Name              Value  Description
================= ====== ===========================
``Edition``       ``1``  Project edition mode
``Visualisation`` ``2``  (Iray) mode
``Baking``        ``4``  Baking mode
================= ====== ===========================
"""

ApplicationMenu = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.ui.ApplicationMenu, __name__)
"""Standard application menus enumeration.

Members:

============= ===========================
Name          Description
============= ===========================
``File``      File menu
``Edit``      Edit menu
``Mode``      Mode menu
``Window``    Window menu
``Viewport``  Viewport menu
``Help``      Help menu
============= ===========================
"""


def show_main_window():
    """Show Substance 3D Painter main window in the windowing system and give it the focus.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    _substance_painter.ui.show_main_window()


def get_main_window() -> PySide6.QtWidgets.QMainWindow:
    """Get access to Substance 3D Painter main window.

    Returns:
        PySide6.QtWidgets.QMainWindow: The application main window.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    return shiboken6.wrapInstance(_substance_painter.ui.get_main_window_ptr(),
                                  PySide6.QtWidgets.QMainWindow)


def get_layout(mode: UIMode) -> bytes:
    """Get Substance 3D Painter layout state for the given UI mode.

    Args:
        mode (UIMode): Selected UI mode.

    Returns:
        bytes: The layout state.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    return _substance_painter.ui.get_layout(mode)


def get_layout_mode(layout: bytes) -> UIMode:
    """Get the Substance 3D Painter UI layout mode of a given state.

    Args:
        layout (bytes): The layout state, obtained with :func:`get_layout`.

    Returns:
        UIMode: The state associated UI mode.

    Raises:
        RuntimeError: In case of incorrect layout data.
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    return _substance_painter.ui.get_layout_mode(layout)


def set_layout(layout: bytes) -> UIMode:
    """Restore a Substance 3D Painter layout state optained with :func:`get_layout`.

    Args:
        layout (bytes): The layout state to be restored.

    Returns:
        UIMode: The restored UI mode.

    Raises:
        RuntimeError: In case of incorrect layout data.
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    return _substance_painter.ui.set_layout(layout)


def reset_layout(mode: UIMode):
    """Reset Substance 3D Painter layout to default for a selected UI mode.

    Args:
        mode (UIMode): Selected UI mode.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    _substance_painter.ui.reset_layout(mode)


def add_dock_widget(widget: PySide6.QtWidgets.QWidget,
                    ui_modes: int = UIMode.Edition) -> PySide6.QtWidgets.QDockWidget:
    """Add a widget as a QDockWidget to the main window.

    If the widget has a ``windowIcon``, it will be used as a quick button to easily
    reopen the QDockWidget when closed. If the widget has a unique ``objectName`` it
    will be used to properly save and restore the dock widget location and geometry.

    Args:
        widget (PySide6.QtWidgets.QWidget): The widget to be added as a dock widget.
        ui_modes (int, optional): A combination of `UIMode` flags.

    Returns:
        PySide6.QtWidgets.QDockWidget: The corresponding dock widget.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    if not widget.isWidgetType():
        raise TypeError("operand must inherit from PySide6.QtWidgets.QWidget")
    dock_pointer = _substance_painter.ui.add_dock_widget(
        shiboken6.getCppPointer(widget)[0], ui_modes)

    return shiboken6.wrapInstance(dock_pointer, PySide6.QtWidgets.QDockWidget)


def add_plugins_toolbar_widget(widget: PySide6.QtWidgets.QWidget):
    """Add a widget to the plugins toolbar.

    Args:
        widget (PySide6.QtWidgets.QWidget): The widget to be added.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    _substance_painter.ui.add_plugins_toolbar_widget(shiboken6.getCppPointer(widget)[0])


def add_menu(menu: PySide6.QtWidgets.QMenu):
    """Add the given menu to the application main window.

    Args:
        menu (PySide6.QtWidgets.QMenu): The menu to be added.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    if not menu.objectName():
        menu.setObjectName("python-addon")
    _substance_painter.ui.add_menu(shiboken6.getCppPointer(menu)[0])


def add_toolbar(title: str,
                object_name: str,
                ui_modes: int = UIMode.Edition) -> PySide6.QtWidgets.QToolBar:
    """Create and add a toolbar to the application main window.

    Args:
        title (str): The title of the toolbar.
        object_name (str): The toolbar object name. A unique object name is mandatory for proper
            save and restore of the UI layout.
        ui_modes (int): A combination of `UIMode` flags.

    Returns:
        PySide6.QtWidgets.QToolBar: The newly created toolbar.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    toolbar_pointer = _substance_painter.ui.add_toolbar(title, object_name, ui_modes)
    return shiboken6.wrapInstance(toolbar_pointer, PySide6.QtWidgets.QToolBar)


def add_action(menu: ApplicationMenu, action: PySide6.QtGui.QAction):
    """Add the given action to the given application menu.

    This will clear the action tooltip.

    Args:
        menu (ApplicationMenu): One of the predefined `ApplicationMenu`.
        action (PySide6.QtGui.QAction): The action to be added.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    _substance_painter.ui.add_action(menu, shiboken6.getCppPointer(action)[0])


def delete_ui_element(element: PySide6.QtWidgets.QWidget):
    """Delete a UI element.

    The element passed as parameter is deleted. After that, any attempt to call a
    method on ``element`` will throw an exception.

    Args:
        element: The UI element to delete.
    """
    shiboken6.delete(element)


def get_current_mode() -> UIMode:
    """
    Get the current UI mode.

    Returns:
        UIMode: The current UI mode.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    return _substance_painter.ui.get_current_mode()


def switch_to_mode(mode: UIMode) -> None:
    """
    Switch to some UI mode.

    Args:
        mode (UIMode): UI mode to switch to.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started its UI service.
    """
    _substance_painter.ui.switch_to_mode(mode)
