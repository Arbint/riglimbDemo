##########################################################################
# ADOBE CONFIDENTIAL
#
# Copyright 2021 Adobe
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
This module allows to evaluate JavaScript code against the legacy embedded
JavaScript engine. This allows to use all the exposed JavaScript API through
Python scripting. The JavaScript API is described in dedicated help accessible
via the ``Help > Scripting documentation > JavaScript API`` menu found in
`Substance 3D Painter` application.

Example:
    ::

        import substance_painter.js

        # Get the baking parameters
        js_code = 'alg.baking.textureSetBakingParameters("some_texture_set")'
        baking_parameters = substance_painter.js.evaluate(js_code)

        # substance_painter.js.evaluate returns JSON, so the result is easy to retrieve and use
        material_parameters = baking_parameters['materialParameters']
        apply_diffusion = material_parameters['commonParameters']['Apply_Diffusion']
"""

import json
import _substance_painter.js


def evaluate(js_code: str) -> str:
    """
    Evaluate a JavaScript expression.
    The JavaScript API is described in dedicated help accessible via the
    ``Help > Scripting documentation > JavaScript API`` menu found in
    `Substance 3D Painter` application.

    Args:
        js_code (str): The block of JavaScript code to be evaluated.

    Returns:
        str: The JSON formated result of the evaluation.

    Raises:
        RuntimeError: If the JavaScript exception evaluation returns an error.
    """
    return json.loads(_substance_painter.js.evaluate(js_code))
