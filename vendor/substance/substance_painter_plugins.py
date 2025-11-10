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
This module allows to manage the `Substance 3D Painter` Plugins: listing existing
Plugins, loading or unloading a given Plugin, etc.

A `Substance 3D Painter` Plugin is a standard Python module, placed in a path added
to :obj:`substance_painter_plugins.path`, which can use the `Substance 3D Painter`
Python API to do certain tasks.

Example:
    ::

        import importlib
        import substance_painter_plugins

        # Get the list of available Plugin names:
        all_plugins_names = substance_painter_plugins.plugin_module_names()
        for name in all_plugins_names:
            print(name)

        # Load the "hello world" Plugin:
        plugin = importlib.import_module("hello_plugin")

        # Start the Plugin if it wasn't already:
        if not substance_painter_plugins.is_plugin_started(plugin):
            substance_painter_plugins.start_plugin(plugin)
"""

import gc
import importlib
import os
from pathlib import Path
import pkgutil
import sys
import traceback

import substance_painter.logging

__version__ = "0.0.1"

path = []
"""
list: A list of strings that specifies the search path for plugins.
Initialized from ``SUBSTANCE_PAINTER_PLUGINS_PATH`` environment variable, `Substance 3D Painter`
installation directory and `Substance 3D Painter` user resources directory.

You need to call explicitly :obj:`substance_painter_plugins.update_sys_path` after updating this
variable.

A plugins directory is expected to contain three subdirectories, automatically added to
``sys.path``:

  * **plugins** : Modules that are loaded as optional components.
  * **startup** : Modules that are always loaded at application startup.
  * **modules** : Utility modules, shared across plugins.

Modules in ``plugins/`` and ``startup/`` directories are expected to have a ``start_plugin()`` and
a ``close_plugin()`` methods, respectively called after loading the module and before unloading it.
Modules added in ``plugins/`` directory take precedence over modules added in ``startup/``
directory.
"""

plugins = {}
"""dict: Currently started plugins."""


def start_plugin(module):
    """
    Start the given `Substance 3D Painter` plugin.

    Args:
        module: A Python module that is expected to have a ``start_plugin`` method.
    """
    if module.__name__ not in plugins:
        module.start_plugin()
        plugins[module.__name__] = module


def close_plugin(module, gc_collect=True):
    """
    Close the given `Substance 3D Painter` plugin.

    Args:
        module: A Python module that is expected to have a ``close_plugin`` method.
        gc_collect: Run a full garbage collection if set to True.
    """
    if module.__name__ in plugins:
        plugins.pop(module.__name__)
        module.close_plugin()
        if gc_collect:
            # Run a full garbage collect to get rid of all object
            # that should be destroyed before closing the application.
            gc.collect()


def is_plugin_started(module):
    """
    Check if the given plugin is currently started.

    Args:
        module: A Python module.

    Returns:
        ``True`` if the given module is currently started, ``False`` otherwise.
    """
    if module.__name__ in plugins:
        return True
    return False


def reload_plugin(module):
    """
    Reload a plugin and start it.

    Read `importlib.reload(module) documentation`_ for possible caveats. See :func:`start_plugin`
    and :func:`close_plugin` for details about starting and closing a plugin. If the plugin has
    a ``reload_plugin`` method, it will be executed after closing and before restarting the plugin.
    The purpose of ``reload_plugin`` method is to reload manually all sub-modules the plugin
    depends on (in case the plugin is a Python package for example).

    Args:
        module: A Python module.

    Returns:
        The reloaded plugin module.

    See also:
        :func:`start_plugin`, :func:`close_plugin`, `importlib.reload(module) documentation`_.

    .. _importlib.reload(module) documentation:
        https://docs.python.org/3/library/importlib.html#importlib.reload
    """
    # We need to be fault tolerant in case module 'close_plugin' method raises an exception
    try:
        close_plugin(module)
    except Exception:  # pylint: disable=broad-except
        sys.stderr.write(f"failed to close {module.__name__} plugin\n")
        traceback.print_exc()
    # The return value is the module object (which can be different
    # if re-importing causes a different object to be placed in sys.modules).
    module = importlib.reload(module)
    if hasattr(module, 'reload_plugin'):
        module.reload_plugin()
    start_plugin(module)
    return module


def _is_plugin_discarded(module_name):
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, 'discard_plugin'):
            return module.discard_plugin()
    except Exception:  # pylint: disable=broad-except
        sys.stderr.write(f"failed to load {module_name} plugin\n")
        traceback.print_exc()
        return True
    return False


def _list_available_plugins(dir_name):
    discovered_plugins = {}
    for path_item in path:
        modules_path = Path(path_item) / dir_name
        for _, module_name, _ in pkgutil.iter_modules([str(modules_path)]):
            # ensure not overriden by another module
            spec = importlib.util.find_spec(module_name)
            if spec:
                if modules_path in Path(spec.origin).parents:
                    if _is_plugin_discarded(module_name):
                        continue
                    discovered_plugins[module_name] = modules_path
            else:
                sys.stderr.write(f"no spec found for module '{module_name}'")
    return discovered_plugins


def startup_module_names():
    """
    List the names of the available *startup* modules.

    Returns:
        list[str]: The names of all the available *startup* modules.
    """
    if 'SUBSTANCE_PAINTER_STARTUP_PLUGINS' in os.environ:
        module_names = os.environ['SUBSTANCE_PAINTER_STARTUP_PLUGINS']
        return module_names.split(':')
    return list(_list_available_plugins('startup').keys())


def plugin_module_names():
    """
    List the names of the available *plugins* modules.

    Returns:
        list[str]: The names of all the available *plugins* modules.
    """
    return list(_list_available_plugins('plugins').keys())


def load_startup_modules():
    """Load all startup modules."""
    for module_name in startup_module_names():
        try:
            module = importlib.import_module(module_name)
            start_plugin(module)
        except Exception:  # pylint: disable=broad-except
            sys.stderr.write(f"failed to load {module_name} plugin\n")
            traceback.print_exc()


def close_all_plugins():
    """Close all started plugins."""
    for module in list(plugins.values()):
        try:
            close_plugin(module, False)
        except Exception:  # pylint: disable=broad-except
            sys.stderr.write(f"failed to close {module.__name__} plugin\n")
            traceback.print_exc()
    # Run a full garbage collect to get rid of all object
    # that should be destroyed before closing the application.
    gc.collect()


def update_sys_path():
    """
    Update ``sys.path`` according to :obj:`substance_painter_plugins.path` and
    ``SUBSTANCE_PAINTER_PLUGINS_PATH`` environment variable.
    """
    try:
        env_path = os.environ['SUBSTANCE_PAINTER_PLUGINS_PATH']
        for item in env_path.split(os.pathsep):
            item = os.path.expandvars(item)
            item = os.path.expanduser(item)
            item = os.path.abspath(item)
            if item not in path:
                path.append(item)
    except KeyError:
        pass
    for path_item in path:
        # 'plugins' modules take precedence over 'startup' modules
        # hence 'plugins' must appears before 'startup'
        for dir_name in ['plugins', 'startup', 'modules']:
            dir_path = os.path.join(path_item, dir_name)
            try:
                sys.path.remove(dir_path)
            except:  # pylint: disable=bare-except
                pass
            sys.path.append(dir_path)


def _main():
    update_sys_path()
    load_startup_modules()
    info = "Plugins:\n"
    info += "Version".ljust(20) + ":" + str(__version__) + "\n"
    info += "Plugins search path".ljust(20) + ":" + str(path) + "\n"
    info += "Loaded plugins".ljust(20) + ":" + str(plugins)
    substance_painter.logging.log(substance_painter.logging.DBG_INFO,
                                  substance_painter.logging.PYTHON_CHANNEL, info)


if __name__ == "__main__":
    _main()
