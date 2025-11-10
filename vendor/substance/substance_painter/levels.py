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
The ``levels`` module define types used to manipulate levels parameters.

This module exposes the corresponding :class:`LevelsParams`, :class:`LevelsParamsMono` and
:class:`LevelsParamsRGB` classes. See :class:`LevelsEffectNode` and :class:`SourceReference`
for usages.
"""

from __future__ import annotations

import dataclasses
from statistics import mean
from typing import Tuple, Union

import _substance_painter.textureset


@dataclasses.dataclass
class LevelsParamsRGB:
    """
    A levels parameters, when in RGB color mode.

    :param input_min: The minimum input threshold.
    :param input_max: The maximum input threshold.
    :param gamma: Gamma.
    :param output_min: The minimum output threshold.
    :param output_max: The maximum output threshold.
    :param clamp: Wether the values should be clamped or not.
    """
    input_min: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    input_max: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    gamma: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    output_min: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    output_max: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    clamp: bool = False


@dataclasses.dataclass
class LevelsParamsMono:
    """
    A levels parameters, when in Luminance or only one color mode.

    :param input_min: The minimum input threshold.
    :param input_max: The maximum input threshold.
    :param gamma: Gamma.
    :param output_min: The minimum output threshold.
    :param output_max: The maximum output threshold.
    :param clamp: Wether the values should be clamped or not.
    """
    input_min: float = 0.0
    input_max: float = 1.0
    gamma: float = 1.0
    output_min: float = 0.0
    output_max: float = 1.0
    clamp: bool = False


LevelsParams = Union[LevelsParamsMono, LevelsParamsRGB]
"""
alias of :class:`LevelsParamsMono` | :class:`LevelsParamsRGB`

Levels parameters can be expressed for three channels (RGB) or only one color channel (only one
color or luminance). `LevelsParams` is used to regroup the two possible parameters flavors.
"""


def _from_private_params(params, is_color):
    """
    Returns a LevelsParamsMono or a LevelsParamsRGB from a _substance_painter.levels.LevelsParams
    depending on `is_mono`.
    """
    if is_color:
        return LevelsParamsRGB(params.input_min, params.input_max, params.gamma, params.output_min,
                               params.output_max, params.clamp)
    return LevelsParamsMono(mean(params.input_min), mean(params.input_max), mean(params.gamma),
                            mean(params.output_min), mean(params.output_max), params.clamp)


def _to_private_params(params):
    """
    Returns a _substance_painter.levels.LevelsParams from a LevelsParamsMono or a LevelsParamsRGB.
    """
    private_params = _substance_painter.levels.LevelsParams()
    private_params.clamp = params.clamp

    if isinstance(params, LevelsParamsRGB):
        private_params.input_min = params.input_min
        private_params.input_max = params.input_max
        private_params.gamma = params.gamma
        private_params.output_min = params.output_min
        private_params.output_max = params.output_max
    else:
        private_params.input_min = [params.input_min] * 3
        private_params.input_max = [params.input_max] * 3
        private_params.gamma = [params.gamma] * 3
        private_params.output_min = [params.output_min] * 3
        private_params.output_max = [params.output_max] * 3

    return private_params
