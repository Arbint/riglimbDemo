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
The ``source`` module allows to manipulate the sources of a layer.

When a layer takes a texture as parameter, the user may want to create this texture on the fly
using an uniform color or a substance, reference an existing texture in his project or an anchor
point in his stack, etc... Source is a concept that hide this diversity behind a generic interface.

Since source objects are tighly coupled to the context they belong to, they can not be created
manually. To create a source, use the dedicated functions to query and edit sources.

* For fill layers see:

  * :meth:`~substance_painter.layerstack.FillLayerNode.get_material_source` and
    :meth:`~substance_painter.layerstack.FillLayerNode.set_material_source` in
    :class:`SourceMode.Material <substance_painter.source.SourceMode>` mode,

  * :meth:`~substance_painter.layerstack.FillLayerNode.get_source` and
    :meth:`~substance_painter.layerstack.FillLayerNode.set_source` otherwise.

* For fill effects see:

  * :meth:`~substance_painter.layerstack.FillEffectNode.get_material_source` and
    :meth:`~substance_painter.layerstack.FillEffectNode.set_material_source` in
    :class:`SourceMode.Material <substance_painter.source.SourceMode>` mode,

  * :meth:`~substance_painter.layerstack.FillEffectNode.get_source` and
    :meth:`~substance_painter.layerstack.FillEffectNode.set_source` otherwise.

* For generators see :meth:`~substance_painter.layerstack.GeneratorEffectNode.get_source` and
  :meth:`~substance_painter.layerstack.GeneratorEffectNode.set_source`

* For filters see :meth:`~substance_painter.layerstack.FilterEffectNode.get_source` and
  :meth:`~substance_painter.layerstack.FilterEffectNode.set_source`

* For substances see :meth:`~substance_painter.source.SourceSubstance.get_source` and
  :meth:`~substance_painter.source.SourceSubstance.set_source`
"""
from __future__ import annotations

import dataclasses
import warnings
from enum import Enum
from typing import Dict, List, Set, Union, Tuple

import _substance_painter
from substance_painter import _utility, layerstack, levels  # pylint: disable=cyclic-import
from substance_painter._utility import ReadOnlyUid
from substance_painter.levels import LevelsParams
from substance_painter.resource import ResourceID
from substance_painter.textureset import ChannelType

from .colormanagement import(
    Color, ResourceColorSpace, _to_private_color, _to_public_color,
    _to_private_color_space, _to_public_color_space)
from .properties import Property, PropertyValue, _to_private_property_value

SourceMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.source.SourceMode, __name__)
"""
When working with a fill layer or a fill effect in a multi-channel context,
you can either have one source that write to all channels or several sources
with each source writing to one channel.

Members:

================= ===========================================================================
Name              Description
================= ===========================================================================
``Split``         Split mode is used when a source write to only one channel.
``Material``      Material mode is used when a source write to multiple channels at once.
================= ===========================================================================

See also:
    :meth:`substance_painter.layerstack.FillLayerNode.source_mode` and
    :meth:`substance_painter.layerstack.FillEffectNode.source_mode`.
"""

class FontResolutionMode(Enum):
    """
    Members:

    ================= ================================================
    Name              Description
    ================= ================================================
    ``Auto``          Resolution is automatically computed.
    ``Manual``        Resolution is manually provided.
    ================= ================================================

    .. warning::
        Deprecated since 0.3.4, use :class:`~substance_painter.source.ResolutionMode` instead.
    """
    Auto = _substance_painter.source.ResolutionMode.Auto  # pylint: disable = invalid-name
    Manual = _substance_painter.source.ResolutionMode.Manual  # pylint: disable = invalid-name

HorizontalAlignment = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.source.HorizontalAlignment, __name__)
"""
Members:

================= =============================
Name              Description
================= =============================
``Left``          Align the text to the left.
``Center``        Center the text horizontally.
``Right``         Align the text to the right.
================= =============================
"""

VerticalAlignment = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.source.VerticalAlignment, __name__)
"""
Members:

================= ===========================
Name              Description
================= ===========================
``Top``           Align the text from the top.
``Middle``        Center the text vertically.
``Bottom``        Align the text from the bottom.
================= ===========================
"""

class ResolutionMode(Enum):
    """
    Members:

    ================= ==================================================
    Name              Description
    ================= ==================================================
    ``Auto``          Resolution matches the parent context, such as the Texture Set
                      resolution in a fill layer, or 512 pixels in a brush tool.
    ``Asset``         Resolution uses the pixel size defined in the vector file.
                      Not applicable for Font resources.
    ``Custom``        Resolution is manually provided.
    ``Document``      Deprecated since 0.3.4, use `Asset` instead.
    ``Manual``        Deprecated since 0.3.4, use `Custom` instead.
    ================= ==================================================
    """
    Auto = _substance_painter.source.ResolutionMode.Auto  # pylint: disable = invalid-name
    Asset = _substance_painter.source.ResolutionMode.Document  # pylint: disable = invalid-name
    Custom = _substance_painter.source.ResolutionMode.Manual  # pylint: disable = invalid-name
    Document = _substance_painter.source.ResolutionMode.Document  # pylint: disable = invalid-name
    Manual = _substance_painter.source.ResolutionMode.Manual  # pylint: disable = invalid-name

VectorialResolutionMode = ResolutionMode
"""
Alias for :class:`ResolutionMode`.

Warning:
   Deprecated since 0.3.4, use :class:`ResolutionMode` instead.
"""

CropAreaMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.source.CropAreaMode, __name__)
"""
Members:

================== ==================================================
Name               Description
================== ==================================================
``DocumentBounds`` The crop area is automatically calculated based on the vector document.
                   This corresponds to the `Asset bounds` option available in Painter's UI.
``Manual``         The crop area is explicitly defined by the user. This corresponds to
                   the `Custom area` option available in Painter's UI.
================== ==================================================
"""

AlphaMatte = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.source.AlphaMatte, __name__)
"""
Members:

=========================== ================================================
Name                        Description
=========================== ================================================
``KeepAlpha``               Keep the alpha.
``ExtractAlpha``            Extract the alpha.
``DefaultBackgroundColor``  Matte the alpha with a default background color.
=========================== ================================================
"""


@dataclasses.dataclass
class ResolutionOverride:
    """
    Resolution override parameters.

    :param mode: Control how the resource rendering resolution is driven.
    :param value: The resolution to use when `mode` is
        :class:`ResolutionMode.Manual <ResolutionMode>`, as [width, height] in pixels.
        Values must be a power of 2, in range [128, 4096].
    """
    mode: ResolutionMode
    value: Tuple[int, int]

    @_utility.restrict_resolution('value', 128, 4096)
    def __setattr__(self, __name: str, __value: dataclasses.Any) -> None:
        super().__setattr__(__name, __value)


def _resolution_override_from_private(value):
    return ResolutionOverride(ResolutionMode(value.mode.value), value.value)


def _resolution_override_to_private(value):
    private_value = _substance_painter.source.ResolutionOverride()
    private_value.mode = _substance_painter.source.ResolutionMode(value.mode.value)
    private_value.value = value.value
    private_value.log2offset = 0
    return private_value


class _ResolutionOverrideDeprecated:  # pylint: disable=no-member
    """Helpers to add deprecated properties for retrocompatibility."""

    @property
    def resolution_mode(self):
        """
        :meta private:
        """
        warnings.warn(
            "resolution_mode is deprecated, use resolution.mode instead", DeprecationWarning)
        return self.resolution.mode

    @resolution_mode.setter
    def resolution_mode(self, value):
        """
        :meta private:
        """
        warnings.warn(
            "resolution_mode is deprecated, use resolution.mode instead", DeprecationWarning)
        self.resolution.mode = value

    @property
    def resolution_value(self):
        """
        :meta private:
        """
        warnings.warn(
            "resolution_value is deprecated, use resolution.value instead", DeprecationWarning)
        return self.resolution.value

    @resolution_value.setter
    def resolution_value(self, value):
        """
        :meta private:
        """
        warnings.warn(
            "resolution_value is deprecated, use resolution.value instead", DeprecationWarning)
        self.resolution.value = value



def _from_id(uid: int) -> Source:
    """
    Instantiate the most specific source type for the given source id.

    Returns:
        Source: The source instance.

    Raises:
        ValueError: If unable to determine the source type.
    """
    if uid is None:
        return None
    classes = {
        _substance_painter.source.SourceType.UniformColor: SourceUniformColor,
        _substance_painter.source.SourceType.Bitmap: SourceBitmap,
        _substance_painter.source.SourceType.Vectorial: SourceVectorial,
        _substance_painter.source.SourceType.Substance: SourceSubstance,
        _substance_painter.source.SourceType.Reference: SourceReference,
        _substance_painter.source.SourceType.Font: SourceFont,
    }
    cls = classes[_substance_painter.source.get_source_type(uid)]
    return cls(uid)


class ActiveChannelsMixin:  # pylint: disable=too-few-public-methods
    """
    Mixin providing active channels property.

    :meta private:
    """

    @property
    def active_channels(self) -> Set[ChannelType]:
        """
        The set of active channels of the source.

        :getter: Returns the active channels of the source. To get the list of channels
            for a given stack, see :meth:`substance_painter.textureset.Stack.all_channels`.
        :setter: Sets the active channels of the source, channels not listed will be
            disabled.
        :type: Set[ChannelType]
        """
        return _substance_painter.source.get_active_channels(self.uid())

    @active_channels.setter
    def active_channels(self, channels: Set[ChannelType]) -> None:
        _substance_painter.source.set_active_channels(self.uid(), channels)


class SourceEditorMixin(ActiveChannelsMixin):
    """
    Mixin providing all necessary functions to edit sources.

    :meta private:
    """

    @property
    def source_mode(self) -> SourceMode:
        """
        The current context in which the source is edited:

        * ``Material``: only one source is used to write to several
          channels, see :func:`~get_material_source` and :func:`~set_material_source`.
        * ``Split``: each source write to a single channel, see :func:`~get_source` and
          :func:`~set_source`.
        * ``None``: the current context is not multi-channel (ex: a mask),
          see :func:`~get_source` and :func:`~set_source`.

        For more details, see :ref:`fill_example`.

        :getter: Returns the source mode.
        :type: SourceMode
        """
        return _substance_painter.source.get_fill_source_mode(self.uid())

    def get_source(self, channeltype: ChannelType | None = None) -> Source:
        """
        Get the source for the given channel type.

        Args:
            channeltype(ChannelType|None): Must be None in mono channel context.

        Returns:
            Source: the source at channel type.

        Raises:
            EditionContextException: If the `channeltype` is not valid in the current context.
                See :attr:`active_channels`.
            RuntimeError: If the source is in :class:`SourceMode.Material <SourceMode>`.
                See :attr:`source_mode`.
        """
        return _from_id(_substance_painter.source.get_fill_source(self.uid(), channeltype))

    def set_source(self, channeltype: ChannelType | None,
                   source: ResourceID | Color | layerstack.AnchorPointEffectNode) -> Source:
        """
        Set the source for the given channel type.

        Args:
            channeltype(ChannelType|None): Must be None in mono channel context.
            source(ResourceID|Color|layerstack.AnchorPointEffectNode): the source parameter.

        Returns:
            Source: the source at channel type.

        Raises:
            EditionContextException: If the `channeltype` is not valid in the current context.
                See :attr:`active_channels`.
            ValueError: If the `source` parameter is not valid.
        """
        if isinstance(source, ResourceID):
            return _from_id(
                _substance_painter.source.set_fill_source(self.uid(), channeltype, source.url()))
        if isinstance(source, Color):
            return SourceUniformColor(
                _substance_painter.source.set_fill_source(
                    self.uid(), channeltype, _to_private_color(source)))
        if isinstance(source, layerstack.AnchorPointEffectNode):
            return SourceReference(
                _substance_painter.source.set_fill_source(self.uid(), channeltype, source.uid()))
        raise ValueError(
            "Unknown parameter type. Only `resource.ResourceID`,"
            " `colormanagement.Color` or `layerstack.AnchorPointEffectNode`"
            " are supported")

    def reset_source(self, channeltype: ChannelType | None = None) -> None:
        """
        Reset the source at channel type.

        Args:
            channeltype(ChannelType|None): Must be None in mono channel context.

        Raises:
            EditionContextException: If the `channeltype` is not valid in the current context.
                See :attr:`active_channels`.
        """
        _substance_painter.source.reset_fill_source(self.uid(), channeltype)

    def get_material_source(self) -> SourceSubstance | SourceReference:
        """
        Get the source in material mode.

        Returns:
            Source: the source.

        Raises:
            RuntimeError: If the source is not in :class:`SourceMode.Material <SourceMode>`.
                See :attr:`source_mode`.
            EditionContextException: If the current context in not multi-channel.
        """
        return _from_id(_substance_painter.source.get_fill_material_source(self.uid()))

    def set_material_source(
            self, source: ResourceID | layerstack.AnchorPointEffectNode
    ) -> SourceSubstance | SourceReference:
        """
        Set the source in material mode.

        Args:
            source(ResourceID|layerstack.AnchorPointEffectNode): the source parameter.

        Returns:
            Source: the source.

        Raises:
            ValueError: If the `source` parameter is not valid.
            EditionContextException: If the current context in not multi-channel.
        """
        if isinstance(source, ResourceID):
            return SourceSubstance(
                _substance_painter.source.set_fill_material_source(self.uid(), source.url()))
        if isinstance(source, layerstack.AnchorPointEffectNode):
            return SourceReference(
                _substance_painter.source.set_fill_material_source(self.uid(), source.uid()))
        raise ValueError(
            "Unknown parameter type. Only `resource.ResourceID` or"
            " `layerstack.AnchorPointEffectNode` are supported")

    def reset_material_source(self) -> None:
        """
        Reset the source in material mode.

        Raises:
            EditionContextException: If the current context in not multi-channel.
        """
        _substance_painter.source.reset_fill_material_source(self.uid())

    def set_sources_from_preset(self, preset: ResourceID) -> None:
        """
        Setup the fill with the given preset.

        Args:
            preset(ResourceID): the resource preset.

        Raises:
            ValueError: If `preset` is not a valid resource preset.
        """
        _substance_painter.source.set_fill_sources_from_preset(self.uid(), preset.url())


class SourceUniformColor(ReadOnlyUid):
    """
    A class that represents an uniform color source.
    """

    def get_color(self) -> Color:
        """
        Get the uniform color of the source.

        :returns: The uniform color used by the source.
        """
        return _to_public_color(_substance_painter.source.get_source_uniform_color(self.uid()))

    def set_color(self, color: Color) -> None:
        """
        Set the uniform color of the source.

        :param color: The desired uniform color.
        """
        _substance_painter.source.set_source_uniform_color(self.uid(), _to_private_color(color))


class SourceBitmap(ReadOnlyUid):
    """
    A class that represents a bitmap source.
    """

    @property
    def resource_id(self) -> ResourceID:
        """
        The current bitmap used by the source.

        :getter: Returns the resource identifier of the bitmap used by the source.
        :type: ResourceID
        """
        return ResourceID.from_url(_substance_painter.source.get_source_bitmap_url(self.uid()))

    def get_color_space(self) -> ResourceColorSpace:
        """
        Return the color space of the bitmap.

        :returns: The current color space.

        See also:
            :ref:`colormanagement_colorspaces` section.
        """
        return _to_public_color_space(
            _substance_painter.source.get_bitmap_color_space(self.uid()))

    def set_color_space(self, color_space: ResourceColorSpace):
        """
        Override the default color space of the bitmap.

        :param color_space: The color space to set.
        :raises ValueError: If the given color space is not supported in the current context
            or by the current color management engine.

        See also:
            :ref:`colormanagement_colorspaces` section, :func:`list_available_color_spaces`.
        """
        _substance_painter.source.set_bitmap_color_space(
            self.uid(),
            _to_private_color_space(color_space))

    def reset_color_space(self):
        """
        Remove any override color space and go back to the default one.
        """
        _substance_painter.source.reset_bitmap_color_space(self.uid())

    def list_available_color_spaces(self) -> List[ResourceColorSpace]:
        """
        Get the list of available color spaces for the bitmap.

        :returns: The list of available color spaces.

        See also:
            :ref:`colormanagement_colorspaces` section.
        """
        return [_to_public_color_space(x)
                for x in _substance_painter.source.list_bitmap_available_color_spaces(self.uid())]



#pylint: disable = too-many-instance-attributes
@dataclasses.dataclass
class SourceFontParams(_ResolutionOverrideDeprecated):
    """
    The source font parameters.

    :param text: The text to render.
    :param auto_size: Automatically adjust size to fit the render resolution.
    :param size: Manual size of the font, normalized and proportional to the resolution.
        Value must be positive.
    :param horizontal_alignment: The horizontal position of the text (left, center, right).
    :param vertical_alignment: The vertical position of the text (top, middle, bottom).
    :param color: The text color as RGB values. Values must be in range [0, 1].
    :param background_color: The RGB background color. Values must be in range [0, 1].
    :param background_opacity: The background opacity value. Value must be in range [0, 1].
    :param line_spacing: Distance between lines of text ("leading") relative to the font size.
    :param character_spacing: The amount of space between adjacent characters relative to
        the font size. Can be negative to subtract spacing.
    :param offset: Horizontal and vertical offset of the text. Normalized to the font size.
    :param resolution: Resolution parameters of the resource.
    :param resolution_mode: Deprecated since 0.3.4. Use ``mode`` attribute from **resolution**
        parameter instead.
    :type resolution_mode: FontResolutionMode
    :param resolution_value: Deprecated since 0.3.4. Use ``value`` attribute from **resolution**
        parameter instead.
    :type resolution_value: Tuple[int, int]
    """
    text: str | None
    auto_size: bool
    size: float | None
    horizontal_alignment: HorizontalAlignment
    vertical_alignment: VerticalAlignment
    color: Color
    background_color: Color
    background_opacity: float | None
    line_spacing: float
    character_spacing: float
    offset: Tuple[float, float]
    resolution: ResolutionOverride

    @_utility.restrict_float_lower_bound('size', 0)
    @_utility.restrict_color('color')
    @_utility.restrict_color('background_color')
    @_utility.restrict_float_range('background_opacity', 0, 1)
    def __setattr__(self, __name: str, __value: dataclasses.Any) -> None:
        super().__setattr__(__name, __value)


class SourceFont(ReadOnlyUid):
    """
    A class that represents a text source.
    """

    @property
    def resource_id(self) -> ResourceID:
        """
        The current font resource of the source.

        :getter: Returns the resource identifier of the font used by the source.
        :type: ResourceID
        """
        return ResourceID.from_url(_substance_painter.source.get_source_font_url(self.uid()))

    def get_parameters(self) -> SourceFontParams:
        """
        Get the source parameters.

        :returns: The source parameters.
        """
        private_params = _substance_painter.source.get_source_font_parameters(self.uid())
        params = SourceFontParams(private_params.text, private_params.auto_size,
                                  private_params.size, private_params.horizontal_alignment,
                                  private_params.vertical_alignment,
                                  _to_public_color(private_params.color),
                                  _to_public_color(private_params.background_color),
                                  private_params.background_opacity, private_params.line_spacing,
                                  private_params.character_spacing, private_params.offset,
                                  _resolution_override_from_private(private_params.resolution))
        return params

    def set_parameters(self, params: SourceFontParams) -> None:
        """
        Set the source parameters.

        :param params: The source parameters.
        :raises ValueError: If the parameters requirements are not met,
            see :class:`SourceFontParams`.
        """
        private_params = _substance_painter.source.SourceFontParams()
        private_params.text = params.text
        private_params.auto_size = params.auto_size
        private_params.size = params.size
        private_params.horizontal_alignment = params.horizontal_alignment
        private_params.vertical_alignment = params.vertical_alignment
        private_params.color = _to_private_color(params.color)
        private_params.background_color = _to_private_color(params.background_color)
        private_params.background_opacity = params.background_opacity
        private_params.line_spacing = params.line_spacing
        private_params.character_spacing = params.character_spacing
        private_params.offset = params.offset
        private_params.resolution = _resolution_override_to_private(params.resolution)
        _substance_painter.source.set_source_font_parameters(self.uid(), private_params)


@dataclasses.dataclass
class SourceVectorialParams(_ResolutionOverrideDeprecated):
    """
    The source vectorial parameters.

    :param artboard_id: The artboard id, for .ai file.
    :param scope: The root element of the hierarchy you want to import.
    :param resolution: Resolution parameters of the resource.
    :param resolution_mode: Deprecated since 0.3.4. Use ``mode`` attribute from **resolution**
        parameter instead.
    :type resolution_mode: ResolutionMode
    :param resolution_value: Deprecated since 0.3.4. Use ``value`` attribute from **resolution**
        parameter instead.
    :type resolution_value: Tuple[int, int]
    :param crop_area_mode: The crop area mode.
    :param crop_area_value: The crop area to use when `crop_area_mode` is `CropAreaMode.Manual`,
        formatted as [left corner x, left corner y, crop area width, crop area height].
        `width` and `height` values must be positive.
    :param fit_to_square: Force the crop area to be square.
    """
    artboard_id: str | None
    scope: str | None
    resolution: ResolutionOverride
    crop_area_mode: CropAreaMode
    crop_area_value: Tuple[float, float, float, float]
    fit_to_square: bool = True

    @_utility.restrict_positive_rect('crop_area_value')
    def __setattr__(self, __name: str, __value: dataclasses.Any) -> None:
        super().__setattr__(__name, __value)


class SourceVectorial(ReadOnlyUid):
    """
    A class that represents a vectorial source.
    """

    @property
    def resource_id(self) -> ResourceID:
        """
        The current vectorial resource of the source.

        :getter: Returns the resource identifier of the vectorial used by the source.
        :type: ResourceID
        """
        return ResourceID.from_url(_substance_painter.source.get_source_vectorial_url(self.uid()))

    def get_parameters(self) -> SourceVectorialParams:
        """
        Get the source parameters.

        :returns: The source parameters.
        """
        private_params = _substance_painter.source.get_source_vectorial_parameters(self.uid())
        params = SourceVectorialParams(private_params.artboard_id, private_params.scope,
                                       _resolution_override_from_private(private_params.resolution),
                                       private_params.crop_area_mode,
                                       private_params.crop_area_value,
                                       private_params.fit_to_square)
        return params

    def set_parameters(self, params: SourceVectorialParams) -> None:
        """
        Set the source parameters.

        :param params: The source parameters.
        :raises ValueError: If the parameters requirements are not met,
            see :class:`SourceVectorialParams`.
        """
        private_params = _substance_painter.source.SourceVectorialParams()
        private_params.artboard_id = params.artboard_id
        private_params.scope = params.scope
        private_params.resolution = _resolution_override_to_private(params.resolution)
        private_params.crop_area_mode = params.crop_area_mode
        private_params.crop_area_value = params.crop_area_value
        private_params.fit_to_square = params.fit_to_square
        _substance_painter.source.set_source_vectorial_parameters(self.uid(), private_params)


class OutputMappingIterator:
    """
    This class implements the iterator interface for class OutputMapping.

    :meta private:
    """

    def __init__(self, uid):
        self.keys = _substance_painter.source.output_mapping_keys(uid)
        self.iterator = iter(self.keys)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)


class OutputMapping(ReadOnlyUid):
    """
    This class gives access to the output mapping of a source procedural in a dict-like fashion.
    See :attr:`~substance_painter.source.SourceSubstance.output_mapping` property.

    Example:

    .. code-block:: python

        import substance_painter as sp
        mapping = a_substance_source.output_mapping
        mapping[sp.textureset.ChannelType.BaseColor] = sp.textureset.ChannelType.Specular
        for channel in mapping:
            print(mapping[channel])

    See also:
        For more technical informations, see the official `KeysView ABCs container
        <https://docs.python.org/3/library/collections.abc.html#collections.abc.KeysView>`_
        documentation as well as `__getitem__
        <https://docs.python.org/3/reference/datamodel.html#object.__getitem__>`_ and
        `__setitem__ <https://docs.python.org/3/reference/datamodel.html#object.__setitem__>`_
        methods.
    """

    def __getitem__(self, key: ChannelType) -> ChannelType:
        return _substance_painter.source.get_active_output(self.uid(), key)

    def __setitem__(self, key: ChannelType, value: str) -> None:
        _substance_painter.source.set_active_output(self.uid(), key, value)

    def __len__(self) -> int:
        return _substance_painter.source.output_mapping_len(self.uid())

    def __contains__(self, key: ChannelType) -> bool:
        return _substance_painter.source.output_mapping_contains(self.uid(), key)

    def __iter__(self) -> OutputMappingIterator:
        return OutputMappingIterator(self.uid())

    # add filtered_keys(): keys filtered by available_channels


class SourceSubstance(ReadOnlyUid):
    """
    A class that represents a procedural source.
    """

    @property
    def resource_id(self) -> ResourceID:
        """
        The current substance resource of the source.

        :getter: Returns the resource of the source.
        :type: ResourceID
        """
        return ResourceID.from_url(_substance_painter.source.get_source_procedural_url(self.uid()))

    @property
    def output_mapping(self) -> OutputMapping:
        """
        The output mapping property in multiple output context.

        :getter: Returns the output mapping property.
        :setter: Sets the output mapping property.
        :type: OutputMapping
        """
        return OutputMapping(self.uid())

    @property
    def active_output(self) -> str:
        """
        The active output of the source in single output context.

        :getter: Returns the output identifier.
        :setter: Sets the output identifier.
        :type: str
        """
        return _substance_painter.source.get_active_output(self.uid(), None)

    @active_output.setter
    def active_output(self, identifier: str) -> None:
        _substance_painter.source.set_active_output(self.uid(), None, identifier)

    @property
    def mask_output(self) -> str:
        """
        The mask output identifier of the source in multiple output context.

        :getter: Returns the mask output identifier.
        :setter: Sets the mask output identifier.
        :type: str
        """
        return _substance_painter.source.get_mask_output(self.uid())

    @mask_output.setter
    def mask_output(self, identifier: str) -> None:
        _substance_painter.source.set_mask_output(self.uid(), identifier)

    @property
    def image_inputs(self) -> List[str]:
        """
        The list of image inputs identifier from the current graph.

        :getter: Returns the list of image inputs identifier.
        :type: List[str]

        See also:
            :class:`substance_painter.properties.Property`
        """
        return _substance_painter.source.get_procedural_inputs(self.uid())

    @property
    def image_outputs(self) -> List[str]:
        """
        The list of image outputs identifier from the current graph.

        :getter: Returns the list of image outputs identifier.
        :type: List[str]
        """
        return _substance_painter.source.get_procedural_outputs(self.uid())

    def get_source(self, identifier: str) -> Source:
        """
        Get the source for the given input identifier.

        :param identifier: The input identifier.
        :returns: the source for the input.
        """
        return _from_id(_substance_painter.source.get_source(self.uid(), identifier))

    def set_source(self, identifier: str,
                   source: ResourceID | Color | layerstack.AnchorPointEffectNode) -> Source:
        """
        Set the source for the given input identifier.

        :param identifier: The input identifier.
        :param source: The source parameter.
        :returns: The source for the input.
        """
        if isinstance(source, ResourceID):
            return _from_id(
                _substance_painter.source.set_source(self.uid(), identifier, source.url()))
        if isinstance(source, Color):
            return SourceUniformColor(
                _substance_painter.source.set_source(
                    self.uid(), identifier, _to_private_color(source)))
        if isinstance(source, layerstack.AnchorPointEffectNode):
            return SourceReference(
                _substance_painter.source.set_source(self.uid(), identifier, source.uid()))
        raise ValueError(
            "Unknown parameter type. Only `resource.ResourceID`,"
            " `colormanagement.Color` or `layerstack.AnchorPointEffectNode`"
            " are supported")

    def reset_source(self, identifier: str) -> None:
        """
        Reset the source for the given input identifier.

        :param identifier: The input identifier.
        """
        _substance_painter.source.reset_source(self.uid(), identifier)

    def remove_source(self, identifier: str) -> None:
        """
        Remove the source for the given input identifier.

        :param identifier: The input identifier.
        """
        _substance_painter.source.remove_source(self.uid(), identifier)

    def get_parameters(self) -> Dict[str, PropertyValue]:
        """
        Get source procedural parameters. For each property of the source,
        the resulting dictionnary holds an entry with the property name as key
        and the property value as value.

        :returns: The source procedural parameters.

        See also:
            :func:`substance_painter.source.SourceSubstance.get_properties`
        """
        return {k: v.value() for k, v in self.get_properties().items()}

    def set_parameters(self, property_values: Dict[str, PropertyValue]) -> None:
        """
        Set source procedural parameters.

        :param property_values: A dict of properties to be set with their corresponding values.

        Warning:
            Boolean parameters are treated as integer, if you use `True` or `False` you will get an
            error message:

            `>>> Bad value for property '<property_name>': expected value of type <int32> but got
            <bool>`
        """
        properties = self.get_properties()

        def get_property(name):
            try:
                return properties[name].handle
            except KeyError as exc:
                raise KeyError(f"Property '{name}' not found") from exc

        values = [(get_property(k), _to_private_property_value(v))
                  for k, v in property_values.items()]
        _substance_painter.source.set_source_procedural_parameters(self.uid(), values)

    def get_properties(self) -> Dict[str, Property]:
        """
        Get source procedural properties.

        :returns: The source procedural properties.

        See also:
            :class:`substance_painter.properties.Property`
        """
        return {
            Property(x).short_name(): Property(x)
            for x in _substance_painter.source.get_source_procedural_parameters(self.uid())
        }

    def get_preset_list(self) -> List[str]:
        """
        Get the list of all available presets for this source.

        :returns: An array of all preset's names available.

        See also:
            :func:`substance_painter.source.SourceSubstance.apply_preset`
        """
        return _substance_painter.source.get_procedural_preset_list(self.uid())

    def apply_preset(self, name: str):
        """
        Apply a preset given its name. If no preset is found with this name nothing is done.

        :param name: The name of the preset to apply.

        See also:
            :func:`substance_painter.source.SourceSubstance.get_preset_list`
        """
        return _substance_painter.source.apply_procedural_preset(self.uid(), name)


class ChannelMappingIterator:
    """
    This class implements the iterator interface for class ChannelMapping.

    :meta private:
    """

    def __init__(self, uid):
        self.keys = _substance_painter.source.channel_mapping_keys(uid)
        self.iterator = iter(self.keys)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iterator)


class ChannelMapping(ReadOnlyUid):
    """
    This class gives access to the active channels of a source reference in a dict-like fashion.
    See :attr:`~substance_painter.source.SourceReference.channel_mapping` property.

    Example:

    .. code-block:: python

        import substance_painter as sp
        mapping = some_SourceReference_object.channel_mapping
        mapping[sp.textureset.ChannelType.BaseColor] = sp.textureset.ChannelType.Specular
        for channel in mapping:
            print(mapping[channel])

    See also:
        For more technical informations, see the official `KeysView ABCs container
        <https://docs.python.org/3/library/collections.abc.html#collections.abc.KeysView>`_
        documentation as well as `__getitem__
        <https://docs.python.org/3/reference/datamodel.html#object.__getitem__>`_ and
        `__setitem__ <https://docs.python.org/3/reference/datamodel.html#object.__setitem__>`_
        methods.
    """

    def __getitem__(self, key: ChannelType) -> ChannelType:
        return _substance_painter.source.get_active_channel(self.uid(), key)

    def __setitem__(self, key: ChannelType, value: ChannelType) -> None:
        _substance_painter.source.set_active_channel(self.uid(), key, value)

    def __len__(self) -> int:
        return _substance_painter.source.channel_mapping_len(self.uid())

    def __contains__(self, key: ChannelType) -> bool:
        return _substance_painter.source.channel_mapping_contains(self.uid(), key)

    def __iter__(self) -> ChannelMappingIterator:
        return ChannelMappingIterator(self.uid())


class SourceReference(ReadOnlyUid):
    """
    A class that represents an reference to an anchor point.
    """

    @property
    def channel_mapping(self) -> ChannelMapping:
        """
        The channels mapping property.

        :getter: Returns the channel mapping property.
        :type: ChannelMapping
        :raises EditionContextException: If the current context of the reference is not
                multi-channel.
        """
        return ChannelMapping(self.uid())

    @property
    def referenced_channel(self) -> ChannelType:
        """
        The referenced channel of the source.

        :getter: Returns the referenced channel of the source.
        :setter: Set the referenced channel of the source.
        :type: ChannelMapping
        :raises EditionContextException: If the current context of the reference is not
                single-channel or if the context of the target anchor point is not
                multi-channel.
        """
        return _substance_painter.source.get_active_channel(self.uid(), None)

    @referenced_channel.setter
    def referenced_channel(self, channeltype: ChannelType) -> None:
        _substance_painter.source.set_active_channel(self.uid(), None, channeltype)

    @property
    def anchor(self) -> layerstack.AnchorPointEffectNode:
        """
        The anchor used by this source.

        :getter: Returns the anchor used by the source.
        :type: layerstack.AnchorPointEffectNode
        """
        uid = _substance_painter.source.get_reference_anchor_uid(self.uid())
        return layerstack.AnchorPointEffectNode(uid) if uid is not None else None

    @property
    def alpha_matte(self) -> AlphaMatte:
        """
        The alpha matte used by this source.

        :getter: Returns the alpha matte of the source.
        :setter: Set the alpha matte of the source.
        :type: AlphaMatte
        """
        return _substance_painter.source.get_reference_alpha_matte(self.uid())

    @alpha_matte.setter
    def alpha_matte(self, alpha_matte: AlphaMatte):
        return _substance_painter.source.set_reference_alpha_matte(self.uid(), alpha_matte)

    def get_levels(self) -> LevelsParams:
        """
        Get the parameters used by the levels of this source.

        :returns: The parameters used by the levels of this source.
        """
        params = _substance_painter.source.get_reference_levels(self.uid())
        is_color = _substance_painter.source.get_reference_levels_is_color(self.uid())
        return levels._from_private_params(params, is_color)  # pylint: disable = protected-access

    def set_levels(self, params: LevelsParams) -> None:
        """
        Set the parameters used by the levels of this source.

        :param params: The parameters used by the levels of this source.
        """
        private_params = levels._to_private_params(params)  # pylint: disable = protected-access
        _substance_painter.source.set_reference_levels(self.uid(), private_params)


Source = Union[SourceUniformColor, SourceBitmap, SourceVectorial, SourceSubstance, SourceReference,
               SourceFont]
