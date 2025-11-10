##########################################################################
# ADOBE CONFIDENTIAL
#
# Copyright 2024 Adobe
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
The ``colormanagement`` module allows to manipulate color with color management

This module exposes the :class:`Color` classes which allow to express color with proper
color management.
"""

from enum import Enum
from typing import Tuple, Union

import _substance_painter.colormanagement

class GenericColorSpace(Enum):
    """
    Generic color spaces valid with any color space engine used.

    Can be used for :class:`Color.color_space <Color>` or resources.

    Members:

    ================= ===========================
    Name              Description
    ================= ===========================
    ``sRGB``          sRGB color space (IEC 61966-2-1:1999 in legacy mode)
    ``Working``       working space used in the current project (Linear sRGB in legacy mode).
    ``Raw``           Raw (no color space conversion).
    ================= ===========================
    """
    sRGB = _substance_painter.colormanagement.GenericColorSpace_.sRGB # pylint: disable = invalid-name
    Working = _substance_painter.colormanagement.GenericColorSpace_.Working # pylint: disable = invalid-name
    Raw = _substance_painter.colormanagement.GenericColorSpace_.Raw # pylint: disable = invalid-name

class LegacyColorSpace(Enum):
    """
    Legacy color spaces.

    Don't use them to override your resource's color spaces, use
    :class:`GenericColorSpace.Working <GenericColorSpace>` or
    :class:`GenericColorSpace.sRGB <GenericColorSpace>` instead.

    Can be used for resources only. Can't be used for :class:`Color.color_space <Color>`.

    Members:

    ================= ===========================
    Name              Description
    ================= ===========================
    ``Linear``        Linear sRGB color space.
    ``sRGB``          sRGB color space (IEC 61966-2-1:1999).
    ================= ===========================
    """
    Linear = _substance_painter.colormanagement.LegacyColorSpace_.Linear # pylint: disable = invalid-name
    sRGB = _substance_painter.colormanagement.LegacyColorSpace_.sRGB # pylint: disable = invalid-name

class DataColorSpace(Enum):
    """
    Data color spaces.

    Color spaces used for not color managed channels such as metallic or height.

    Can be used for resources only. Can't be used for :class:`Color.color_space <Color>`.

    Members:

    ================= ===========================
    Name              Description
    ================= ===========================
    ``Data``          Data values, unsigned normalized or float.
    ``DataSigned``    Signed -1..1 data values stored as 0..1 normalized values.
    ================= ===========================
    """
    Data = _substance_painter.colormanagement.LegacyColorSpace_.Data # pylint: disable = invalid-name
    DataSigned = _substance_painter.colormanagement.LegacyColorSpace_.DataSigned # pylint: disable = invalid-name

class NormalColorSpace(Enum):
    """
    Normal color spaces.

    Color spaces used for normal channels to specify how to interpret normal data.

    Can be used for resources only. Can't be used for :class:`Color.color_space <Color>`.

    Members:

    ================== ===========================
    Name               Description
    ================== ===========================
    ``NormalXYZRight`` Normal map in OpenGL format.
    ``NormalXYZLeft``  Normal map in Direct3D format.
    ================== ===========================
    """
    NormalXYZRight = _substance_painter.colormanagement.LegacyColorSpace_.NormalXYZRight # pylint: disable = invalid-name
    NormalXYZLeft = _substance_painter.colormanagement.LegacyColorSpace_.NormalXYZLeft # pylint: disable = invalid-name

ColorColorSpace = Union[GenericColorSpace, str]
ResourceColorSpace = Union[GenericColorSpace, LegacyColorSpace, DataColorSpace,
                           NormalColorSpace, str]

def _to_private_color_space(public_color_space):
    if public_color_space is None:
        return public_color_space

    for passthru_type in [_substance_painter.colormanagement.GenericColorSpace_,
                         _substance_painter.colormanagement.LegacyColorSpace_,
                         str]:
        if isinstance(public_color_space, passthru_type):
            return public_color_space
    return public_color_space.value

def _to_public_color_space(private_color_space):
    if isinstance(private_color_space, str):
        return private_color_space

    # Special case for legacy raw color space. Don't expose it and
    # translate it directly to the generic raw value
    if (isinstance(private_color_space, _substance_painter.colormanagement.LegacyColorSpace_)  and
        private_color_space == _substance_painter.colormanagement.LegacyColorSpace_.Raw):
        return GenericColorSpace.Raw

    for public_enum in [GenericColorSpace, LegacyColorSpace, DataColorSpace, NormalColorSpace]:
        for public_value in public_enum:
            if (isinstance(public_value.value, type(private_color_space))  and
                public_value.value == private_color_space):
                return public_value

    raise RuntimeError(f"invalid private enum: {private_color_space}")

class Color:
    """
    Describe a color (with a color space).

    If you are not confortable with color spaces, you can create a color without
    specifying the colorspace of the data. In this case the color space will be
    deduced depending on the context where this color is used
    (:class:`GenericColorSpace.sRGB <GenericColorSpace>` when used on a color managed
    channel, :class:`GenericColorSpace.Raw <GenericColorSpace>` otherwise).

    On color managed channel, we assume sRGB because it is the most common
    color space used for computer screens, this is why many color pickers will give you
    sRGB data. sRGB is also the standard color space for the web, so a lot of color
    data you can get from the web will be sRGB encoded.

    *A color object returned by the different accessor of our API will always have a
    defined colorspace.*

    :ivar value_raw: raw r,g,b data encoded in `color_space`.
    :vartype value_raw: Tuple[float, float, float]
    :ivar color_space: Color space in which `value_raw`
        is encoded. If None, will be deduced depending on the context where this color
        is used (:class:`GenericColorSpace.sRGB <GenericColorSpace>` when used on
        a color managed channel, :class:`GenericColorSpace.Raw <GenericColorSpace>`
        otherwise).
    :vartype color_space: GenericColorSpace | str
    :param r: Red component
    :param g: Green component
    :param b: Blue component
    :param color_space: Color space in which the data are encoded.
        If not specified, it will be deduced depending on the context where the color
        is used (:class:`GenericColorSpace.sRGB <GenericColorSpace>` when used on
        a color managed channel, :class:`GenericColorSpace.Raw <GenericColorSpace>`
        otherwise) (default: None).
    """

    value_raw: Tuple[float, float, float]
    color_space: ColorColorSpace

    def __init__(self,
                 r: float, # pylint: disable = invalid-name
                 g: float, # pylint: disable = invalid-name
                 b: float, # pylint: disable = invalid-name
                 color_space: ColorColorSpace = None):
        """
        Color constructor
        """

        self.value_raw = (r,g,b)
        self.color_space = color_space

    def __expect_convert(self, color_space):
        if self.color_space is None:
            raise RuntimeError('color_space is undefined, no conversion can be done.')
        return self.__convert(_to_private_color_space(color_space))

    def __convert(self, color_space):
        if self.color_space is None:
            return self.value_raw
        return _substance_painter.colormanagement.transform_cs(
            self.value_raw,
            _to_private_color_space(self.color_space),
            _to_private_color_space(color_space))

    def convert(self, color_space: ColorColorSpace) -> Tuple[float, float, float]:
        """
        Get r,g,b values encoded in the given color space

        Args:
            color_space: Color space in which you want the data encoded to.

        Returns:
            Tuple[float, float, float]: r,g,b data encoded in the given color space

        Raises:
            RuntimeError: if :class:`Color.color_space <Color>` is None
        """
        return self.__expect_convert(color_space)

    @property
    def value(self) -> Tuple[float, float, float]:
        """
        color value

        :getter: Returns the color encoded in sRGB if :class:`Color.color_space <Color>`
            is defined and not :class:`GenericColorSpace.Raw <GenericColorSpace>`,
            otherwise return :class:`Color.value_raw <Color>`.
        :type: Tuple[float, float, float]
        """
        return self.__convert(GenericColorSpace.sRGB)

    @property
    def sRGB(self) -> Tuple[float, float, float]: # pylint: disable = invalid-name
        """
        color value in sRGB space

        :getter: Returns the color value encoded in sRGB
        :setter: Set the color value as sRGB encoded value
        :type: Tuple[float, float, float]
        :Raises: RuntimeError: if :class:`Color.color_space <Color>` is None
        """
        return self.__expect_convert(GenericColorSpace.sRGB)

    @sRGB.setter
    def sRGB(self, value: Tuple[float, float, float]) -> None: # pylint: disable = invalid-name
        self.value_raw = value
        self.color_space = GenericColorSpace.sRGB

    @property
    def working(self) -> Tuple[float, float, float]:
        """
        color value in working space

        :getter: Returns the color value encoded in working space
        :setter: Set the color value as working space encoded value
        :type: Tuple[float, float, float]
        :Raises: RuntimeError: if :class:`Color.color_space <Color>` is None
        """
        return self.__expect_convert(GenericColorSpace.Working)

    @working.setter
    def working(self, value: Tuple[float, float, float]) -> None:
        self.value_raw = value
        self.color_space = GenericColorSpace.Working

def _to_private_color(public_color):
    private_color = _substance_painter.colormanagement.Color()
    private_color.value = public_color.value_raw
    private_color.color_space = _to_private_color_space(public_color.color_space)
    return private_color

def _to_public_color(private_color) -> Color:
    return Color(
        *private_color.value,
        _to_public_color_space(private_color.color_space))
