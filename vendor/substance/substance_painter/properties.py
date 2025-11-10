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
The ``properties`` module introduces the description of dynamic attributes.
"""

import dataclasses
import typing
import json
import _substance_painter.data_tweak
import _substance_painter.colormanagement
from .colormanagement import Color, _to_public_color, _to_private_color

# yapf: disable
PropertyValue = typing.Union[
    bool,
    int,
    typing.Tuple[int, int],
    typing.Tuple[int, int, int],
    typing.Tuple[int, int, int, int],
    float,
    typing.Tuple[float, float],
    typing.Tuple[float, float, float],
    Color,
    typing.Tuple[Color, float],
    typing.Tuple[float, float, float,float],
    str
]

def _to_private_property_value(value):
    if isinstance(value, Color):
        return _to_private_color(value)
    if isinstance(value, tuple) and list(map(type, value)) == [Color, float]:
        return (_to_private_color(value[0]), value[1])
    return value

def _to_public_property_value(value) -> PropertyValue:
    if isinstance(value, _substance_painter.colormanagement.Color):
        return _to_public_color(value)
    if (isinstance(value, tuple) and
        list(map(type, value)) == [_substance_painter.colormanagement.Color, float]):
        return (_to_public_color(value[0]), value[1])
    return value

# yapf: enable
@dataclasses.dataclass(frozen=True)
class Property:
    """
    Read only access to a property data.
    """

    handle: _substance_painter.data_tweak.PythonTweak

    def value(self) -> PropertyValue:
        """
        Get the current property value.

        Returns:
            PropertyValue: the current value.
        """
        return _to_public_property_value(self.handle.value())

    def name(self) -> str:
        """
        Get the property name.

        Returns:
            str: The property name.
        """
        return self.handle.name()

    def short_name(self) -> str:
        """
        Get the shortened property name.

        Returns:
            str: The property short name.
        """
        return self.name().split('.')[-1]

    def label(self) -> str:
        """
        Get the property label.

        Returns:
            str: The property label.
        """
        return self.handle.label()

    def widget_type(self) -> str:
        """
        Get the widget type that should be used to edit the property.

        Returns:
            str: One of: 'Slider', 'Angle', 'Color', 'Togglebutton',
            'Combobox', 'RandomSeed', 'File', 'FileList', 'LineEdit',
            'Resource', 'TextEdit'.
        """
        return self.handle.widget_type()

    def enum_values(self) -> typing.Dict[str, int]:
        """
        The possible enum values with corresponding text for 'Combobox'
        widget type.

        Returns:
            typing.Dict[str, int]: Enum label to enum value dictionary.
        """
        return dict(self.handle.enum_values())

    def enum_value(self, enum_label: str) -> int:
        """
        Get the enum value for the given enum label for 'Combobox'
        widget type.

        Args:
            enum_label (str): A valid enum label.

        Returns:
            typing.Dict[str, int]: The enum value for the corresponding label.
        """
        return self.enum_values()[enum_label]

    def properties(self) -> typing.Dict[str, typing.Any]:
        """
        Get a json object that describes all available meta properties of this
        property. For example: value range, editor step, possible values, tooltip, etc.

        Returns:
            typing.Dict[str, typing.Any]: A json object.
        """
        return json.loads(self.handle.properties())
