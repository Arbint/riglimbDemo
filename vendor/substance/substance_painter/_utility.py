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

"""Utilities used by substance_painter sub-modules.
"""

import dataclasses
import enum
import warnings


def is_mock(obj):
    """Returns ``True`` if 'obj' is a mock, ``False`` otherwise.

    Just check if the unittest.moc.Mock.side_effect method exists.
    WARNING: don't try to use 'isinstance' because mock object
    appears as mocked object.
    """
    return hasattr(obj, "side_effect")


def expose_private_obj(obj, module_name, fields=None, class_name=None):
    """This method allows for proper documentation generation when exposing
    an object form the private API through the public API. The corresponding
    object needs to be documented from python or sphinx files (doc strings
    from the private API wont be imported during documentation generation, but
    they will still be available at runtime to be used with the `help`
    builtin function).

    Returns 'obj' if not a mock object. Otherwise, inject a class with the same
    class name in the module 'module_name'. Optionally a list of 'fields' can
    be supplied if necessary for documention generation.
    """
    if is_mock(obj):
        return enum.Enum(class_name or obj.__class__.__name__, fields or [], module=module_name)
    return obj


def type_mismatch_error_message(argument_name: str, expected_argument_type) -> str:
    """Returns a formatted error message for TypeError exceptions.
    """

    def fully_qualified_type_name(type_object):
        module = type_object.__module__
        name = type_object.__qualname__
        if module is not None and module != "builtins":
            name = module + "." + name
        return name

    type_name = fully_qualified_type_name(expected_argument_type)
    return f"'{argument_name}' should be of type '{type_name}'"


def _flatten_attributes(src, dst, overrides, parent_name="", sep="_"):
    for field in dataclasses.fields(src):
        field_instance = getattr(src, field.name)
        flat_field_name = sep.join([parent_name, field.name]) if parent_name else field.name
        if dataclasses.is_dataclass(field_instance):
            _flatten_attributes(field_instance, dst, overrides, flat_field_name, sep)
        else:
            dst_field_name = overrides.get(flat_field_name, flat_field_name)
            setattr(dst, dst_field_name, field_instance)


def flatten_attributes(src, dst, overrides=None):
    """Flatten all attributes from src hierarchy in dst."""
    assert dataclasses.is_dataclass(src)
    if overrides is None:
        overrides = {}
    _flatten_attributes(src, dst, overrides)


def _unflatten_attributes(src, dst, overrides, parent_name="", sep="_"):
    for field in dataclasses.fields(dst):
        field_instance = getattr(dst, field.name)
        flat_field_name = sep.join([parent_name, field.name]) if parent_name else field.name
        if dataclasses.is_dataclass(field_instance):
            _unflatten_attributes(src, field_instance, overrides, flat_field_name, sep)
        else:
            dst_field_name = overrides.get(flat_field_name, flat_field_name)
            setattr(dst, field.name, getattr(src, dst_field_name))


def unflatten_attributes(src, dst, overrides=None):
    """Load all attributes from src flat object into dst hierarchy."""
    assert dataclasses.is_dataclass(dst)
    if overrides is None:
        overrides = {}
    _unflatten_attributes(src, dst, overrides)


def is_power_of_two(val: int) -> bool:
    """Returns true if val is a power of 2, false otherwise"""
    return (val != 0) and (val & (val - 1) == 0)


def restrict_float_range(name: str, lower_bound: float, upper_bound: float):
    """__set_attr__ decorator to enforce a lower and upper bound on a float value."""

    def inner(set_attr) -> None:

        def wrapped(self, __name, __value):
            if __name == name:
                if __value < lower_bound or __value > upper_bound:
                    raise ValueError(f"Attribut '{name}': value should "
                                     f"always be in [{lower_bound}, {upper_bound}] range")
            set_attr(self, __name, __value)

        return wrapped

    return inner


def restrict_float_lower_bound(name: str, lower_bound: float):
    """__set_attr__ decorator to enforce a lower bound on a float value."""

    def inner(set_attr) -> None:

        def wrapped(self, __name, __value):
            if __name == name:
                if __value < lower_bound:
                    raise ValueError(
                        f"Attribut '{name}': value should always be superior to {lower_bound}")
            set_attr(self, __name, __value)

        return wrapped

    return inner


def restrict_color(name: str):
    """
    __set_attr__ decorator to make sure the modified value is a list of 3 values always
    between 0 and 1.
    """

    def inner(set_attr) -> None:

        def wrapped(self, __name, __value):
            if __name == name:
                for val in __value.value_raw:
                    val = float(val)
                    if (val < 0.0 or val > 1.0):
                        raise ValueError(
                            f"Attribut '{name}': color values should be normalized between 0 and 1")
            set_attr(self, __name, __value)

        return wrapped

    return inner


def restrict_resolution(name: str, lower_bound: int, upper_bound: int):
    """
    __set_attr__ decorator to make sure the resolution is always a power
    of 2 value and in range [lower_bound, upper_bound].
    """

    def inner(set_attr) -> None:

        def wrapped(self, __name, __value):
            if __name == name:
                assert len(__value) == 2, (f"Attribut '{name}': resolution should be a list "
                                           "of 2 values.")
                for val in __value:
                    val = int(val)
                    if not is_power_of_two(val):
                        raise ValueError(
                            f"Attribut '{name}': resolution values should be a power of 2")
                    if val < lower_bound or val > upper_bound:
                        raise ValueError(
                            f"Attribut '{name}': "
                            f"resolution values should always be superior to {lower_bound} "
                            f"and inferior to {upper_bound}")
            set_attr(self, __name, __value)

        return wrapped

    return inner


def restrict_positive_rect(name: str):
    """__set_attr__ decorator to make sure the rect is positive."""

    def inner(set_attr) -> None:

        def wrapped(self, __name, __value):
            if __name == name:
                assert len(__value) == 4, (f"Attribut '{name}': rectangle should be a list "
                                           "of 4 values.")
                [_, _, width, height] = __value
                if width < 0 or height < 0:
                    raise ValueError(
                        f"Attribut '{name}': rectangle's width and height should always "
                        "be positive.")
            set_attr(self, __name, __value)

        return wrapped

    return inner


class ReadOnlyUid:
    """Class with a read-only uid"""

    def __init__(self, uid):
        super().__setattr__('_uid', uid)

    def __setattr__(self, name, value):
        if name == '_uid':
            raise AttributeError("uid is read-only")
        super().__setattr__(name, value)

    def __eq__(self, other):
        return other.__class__ is self.__class__ and self.uid() == other.uid()

    def uid(self) -> int:
        """
        Get the object internal uid.

        Returns:
            int: The internal identifier of the object as an integer.
        """
        return super().__getattribute__('_uid')

    def __repr__(self):
        return f'{self.__class__.__name__}({self.uid()})'


def make_callable(value):
    """Make value callable, usefull when migrating from getter to property."""
    assert not callable(value), "value type should not be callable."
    msg = "This method is deprecated, use the property with the same name instead."

    class CallableValue(type(value)):  # pylint: disable=too-few-public-methods
        """A callable that returns itself."""

        def __call__(self):
            warnings.warn(msg)
            return self

    return CallableValue(value)
