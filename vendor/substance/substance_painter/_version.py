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
Declare once and for all the version of the Python API.

To be used anywhere it is needed, without unwanted dependencies:
__init__.py of the module, conf.py of Sphinx.
"""

__version_info__ = (0, 3, 4)

__version__ = ".".join(str(n) for n in __version_info__)
