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
The ``layerstack`` module allows to manipulate the layer stack of Substance 3D Painter.

This module exposes the corresponding :class:`Node` and :class:`LayerNode` classes.
They allow to discover and manipulate layer stack structure and effects, retrieve and set
information of their state and settings.

To manipulate the layerstack, a project must be opened and must be in edition state.

:func:`get_root_layer_nodes` is the entry point to start querying some layer stack.
"""

from __future__ import annotations
import dataclasses
from enum import Enum
from typing import List, Optional, Union, Dict, ClassVar

import substance_painter.resource
import substance_painter.source
from substance_painter import levels
from substance_painter._utility import ReadOnlyUid
from substance_painter.levels import LevelsParams
from substance_painter.source import ActiveChannelsMixin, SourceEditorMixin, SourceSubstance
from substance_painter.textureset import ChannelType, UVTile, Stack, TextureSet
import _substance_painter.layerstack
import _substance_painter.resource
import _substance_painter.textureset
from . import _utility
from .colormanagement import Color, _to_private_color, _to_public_color

BlendingMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.BlendingMode, __name__)
"""
Blending Modes allow to mix the result of a layer with the other layers below in different manners.
For more information, see the `Blending modes documentation`_.

.. _Blending modes documentation:
    https://helpx.adobe.com/substance-3d-painter/interface/layer-stack/blending-modes.html

Members:

=========================== ===========================================
Name                        Description
=========================== ===========================================
``Normal``                  Displays the Top layer over the Bottom layer without transformation.
``PassThrough``             Flattens the Bottom layer into the Top layer.
``Disable``                 Discards the blending of the layer, displaying only the previous layers.
``Replace``                 Overwrites the Bottom layer.
``Multiply``                Multiplies the Top layer over the Bottom layer.
``Divide``                  Divides the layers below by the color information of the current layer.
``InverseDivide``           Identical to `Divide` but the Top and Bottom layer are exchanged in the
                            blending operation.
``Darken``                  Keeps the minimum color value between the Top and the Bottom layer.
``Lighten``                 Keeps the maximum color value between the Top and the Bottom layer.
``LinearDodge``             Adds the Top layer color value to the Bottom layer.
``Subtract``                Subtracts the Top layer Color from the Bottom layer.
``InverseSubtract``         Identical to `Subtract` but the Top and Bottom layer are exchanged in
                            the blending operation.
``Difference``              Subtracts the Top layer Color from the Bottom Layer, but take the
                            absolute value of the result
``Exclusion``               Similar to `Difference` but it will produce a result with a lower
                            contrast.
``SignedAddition``          Both Adds and Subtracts Color information from the Bottom layer based
                            on the Top layer colors.
``Overlay``                 Combines both `Screen` and `Multiply` Blending Modes.
``Screen``                  Inverts then multiplies color information from the Top and Bottom layer.
                            This result is then inverted again.
``LinearBurn``              Adds the Top and Bottom layer Color information together and then
                            subtract 1 from the result.
``ColorBurn``               Divides the Bottom layer by the Top layer.
``ColorDodge``              Divides the Bottom Layer by the inverted Top layer.
``SoftLight``               Similar to `Overlay`, but applied with a different curve to blend the
                            Color information (less contrasted image).
``HardLight``               Similar to `Overlay`, but the order of operations is inverted.
``VividLight``              Combines `ColorDodge` and `ColorBurn` blending modes.
``LinearLight``             Combines `LinearDodge` and `LinearBurn`.
``PinLight``                Lightens and darkens color information based on the Top layer colors.
``Tint``                    Keeps only the Hue of the Top Layer and uses the Saturation and Value
                            of the Bottom Layer.
``Saturation``              Keeps only the Saturation of the Top Layer and uses the Hue and Value
                            of the Bottom Layer.
``Color``                   Keeps only the Hue and Saturation of the Top Layer and uses the Value
                            of the Bottom Layer.
``Value``                   Keeps only the Value of the Top Layer and uses the Hue and Saturation
                            of the Bottom Layer.
``NormalMapCombine``        Whiteout Blending operation. Preserve details while making sure flat
                            normals still operate properly.
``NormalMapDetail``         Detail Oriented Blending operation (Reoriented Normal Mapping), more
                            precise than Normal Map Combine.
``NormalMapInverseDetail``  Same as `NormalMapDetail`, but it is the Bottom layer that is
                            transformed to fit the surface of the Top layer.
=========================== ===========================================

"""

NodeType = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.NodeType, __name__)
"""
For more information about layers and effects, see :ref:`layerstack_layers_effects`.

Members:

======================== ===========================================
Name                     Description
======================== ===========================================
``PaintLayer``           A layer that can be painted on with brushes and particles.
``PaintEffect``          An effect that can be painted on with brushes and particles.
``FillLayer``            A layer that takes a material or resources as input.
``FillEffect``           An effect that takes a material or resources as input.
``GeneratorEffect``      An effect that takes a Generator substance as input.
``FilterEffect``         An effect that takes a Filter substance as input.
``LevelsEffect``         An effect used to adjust the color ranges of an image.
``CompareMaskEffect``    An effect that compare two channels and produce a mask as a result.
``ColorSelectionEffect`` An effect that extract one or more colors from a bitmap to build a mask.
``GroupLayer``           A layer that contains other layers.
``InstanceLayer``        A layer that allows to synchronize layer parameters across multiple layers
                         and Texture Sets
``AnchorPointEffect``    An effect that allows to expose any resource or element in the layer stack
                         and reference it in different areas
======================== ===========================================
"""


class NodeStack(Enum):
    """
    Indicate which node stack you want to insert in.

    Members:

    ================= ===========================
    Name              Description
    ================= ===========================
    ``Substack``      Insert in the substack of a node (only valid for a Folder node).
    ``Content``       Insert in the content stack of the node.
    ``Mask``          Insert in the mask stack of the node.
    ================= ===========================
    """
    Substack = _substance_painter.layerstack.InsertPositionLocation.Substack  # pylint: disable = invalid-name
    Content = _substance_painter.layerstack.InsertPositionLocation.Content  # pylint: disable = invalid-name
    Mask = _substance_painter.layerstack.InsertPositionLocation.Mask  # pylint: disable = invalid-name


MaskBackground = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.MaskBackground, __name__)
"""
Members:

================= ===========================================
Name              Description
================= ===========================================
``Black``         Everything is dicarded by default.
``White``         Everything is included by default.
================= ===========================================
"""

ColorSelectionBackgroundColor = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.ColorSelectionBackgroundColor, __name__)
"""
Members:

================= ===========================================
Name              Description
================= ===========================================
``Transparent``   Filter background is transparent.
``Black``         Filter background is black.
``White``         Filter background is white.
``Gray``          Filter background is grey.
================= ===========================================
"""

GeometryMaskType = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.GeometryMaskType, __name__)
"""
Members:

================= ===========================================
Name              Description
================= ===========================================
``Mesh``          The geometry mask will apply to mesh names.
``UVTile``        The geometry mask will apply to uv tiles.
================= ===========================================
"""

ProjectionMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.ProjectionMode, __name__)
"""
See `Fill projections documentation`_ for a complete
description of all Projection modes.

.. _Fill projections documentation:
    https://helpx.adobe.com/substance-3d-painter/painting/fill-projections.html

Members:

================ ===========================
Name             Description
================ ===========================
``Fill``         Fill (match per UV Tile) is a special 2D projection useful for UV Tile projects.
``UV``           2D projection that only works in the 2D texture space.
``Triplanar``    3D projection that combines multiple planar projections together.
``Planar``       3D projection that projects an image in a direction as a plane.
``Spherical``    3D projection that projects images and patterns around an object following a sphere
                 area.
``Cylindrical``  3D projection that projects images and patterns around an object following a
                 cylinder area.
``Warp``         3D projection that deforms a texture by editing points of a grid.
``UVSetToUVSet`` Projection from an additional UV set to the current UV set.
================ ===========================
"""

FilteringMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.FilteringMode, __name__)
"""
Members:

================= ===========================
Name              Description
================= ===========================
``BilinearHQ``    Advanced bilinear filtering.
``BilinearSharp`` Simple bilinear filtering.
``Nearest``       No filtering.
================= ===========================
"""

UVWrapMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.UVWrapMode, __name__)
"""
Members:

======================= ===================================
Name                    Description
======================= ===================================
``RepeatNone``          No repeat.
``RepeatHorizontally``  Repeat horizontally.
``RepeatVertically``    Repeat vertically.
``Repeat``              Repeat horizontally and vertically.
======================= ===================================
"""

ShapeCropMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.ShapeCropMode, __name__)
"""
Members:

======================= ==================================
Name                    Description
======================= ==================================
``CroppedToShape``      The projection is confined within the projection area.
``ExtendsOutsideShape`` The projection continues beyond the projection area.
======================= ==================================
"""

ScaleMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.ScaleMode, __name__)
"""
Members:

======================== ==================================
Name                     Description
======================== ==================================
``Factors``              The texture is repeated by a number of times.
``MaterialPhysicalSize`` Automatic adjustement of the texture according to the mesh size and texture
                         size.
``CustomPhysicalSize``   Specify a physical size manually and adapt to the mesh size.
======================== ==================================
"""

CompareMaskEffectOperand = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.CompareMaskEffectOperand, __name__)
"""
See `Compare Mask effect documentation`_ for a complete
description of the compare mask effect.

.. _Compare Mask effect documentation:
    https://helpx.adobe.com/substance-3d-painter/features/effects/compare-mask.html

Members:

================= ===========================
Name              Description
================= ===========================
``LayersBelow``   Flattened version of all the layers below the current one.
``ThisLayer``     This layer only.
``ThisMask``      Existing content of the mask.
``Constant``      Uniform value.
================= ===========================
"""

CompareMaskEffectOperation = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.CompareMaskEffectOperation, __name__)
"""
Members:

=================== ===========================
Name                Description
=================== ===========================
``LesserThan``      Output white values if source has lower values than the target.
``WithinTolerance`` Output white values if source has similar values than the target.
``GreaterThan``     Output white values if source has higher values than the target.
=================== ===========================
"""

SelectionType = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.layerstack.SelectionType, __name__)
"""
Members:

=================== ===========================
Name                Description
=================== ===========================
``Content``         Select the layer content
``Mask``            Select the layer mask
``GeometryMask``    Select the layer geometry mask
``Properties``      Select the layer properties. Only available for instances.
=================== ===========================
"""


class ScopedModification:
    """
    :class:`ScopedModification` can be used to group many layerstack modification calls
    in a single undoable command.

    `name` will be displayed in the software history.

    This object is usefull to:
       * Avoid poluting the history by grouping logically layerstack
         modifications behind a unique name.
       * The computation will only happen when we leave the ``with`` statement
         meaning that we don't waste time computing intermedietary result that we
         don't need.

    This object is a context manager usable with the python ``with`` statement

    Example:
        .. code-block:: python

            import substance_painter as sp

            def insert_many_fills():
                # Insert many layers inside the current texture set layer stack
                # and set their projection mode to tri-planar
                insert_position = sp.layerstack.InsertPosition.from_textureset_stack(
                    sp.textureset.get_active_stack())
                fill = sp.layerstack.insert_fill(insert_position)
                fill.set_projection_mode(sp.layerstack.ProjectionMode.Triplanar)
                fill = sp.layerstack.insert_fill(insert_position)
                fill.set_projection_mode(sp.layerstack.ProjectionMode.Triplanar)
                fill = sp.layerstack.insert_fill(insert_position)
                fill.set_projection_mode(sp.layerstack.ProjectionMode.Triplanar)

            # Calling this method will generate many history entries (1 for each
            # inserted fill and 1 for each projection mode update) and
            # Substance Painter will compute the textures each time a modification
            # happens.
            #
            # Expected history:
            #   * Add fill
            #   * Update projection mode
            #   * Add fill
            #   * Update projection mode
            #   * Add fill
            #   * Update projection mode
            #
            # Potential texture update in the viewport: 6 (one for each modification)
            insert_many_fills()

            # With the ScopedModification below, only one entry will be added to Painter
            # history. A single undo will remove all the fill inserted inside the

            # Calling this method inside a ScopedModification will only generate one history
            # entry and Substance Painter will compute the textures only once.
            #
            # Expected history:
            #   * Insert many layers
            #
            # Potential texture update in the viewport: 1
            with sp.layerstack.ScopedModification("Insert many layers"):
                insert_many_fills()

    """

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        _substance_painter.layerstack.start_macro(self.name)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        _substance_painter.layerstack.end_macro()


def _node_id_to_concrete_node(node_id: int) -> LayerNode:
    concrete_node_type = {
        NodeType.GroupLayer: GroupLayerNode,
        NodeType.PaintLayer: PaintLayerNode,
        NodeType.FillLayer: FillLayerNode,
        NodeType.InstanceLayer: InstanceLayerNode,
        NodeType.GeneratorEffect: GeneratorEffectNode,
        NodeType.PaintEffect: PaintEffectNode,
        NodeType.FillEffect: FillEffectNode,
        NodeType.LevelsEffect: LevelsEffectNode,
        NodeType.CompareMaskEffect: CompareMaskEffectNode,
        NodeType.FilterEffect: FilterEffectNode,
        NodeType.ColorSelectionEffect: ColorSelectionEffectNode,
        NodeType.AnchorPointEffect: AnchorPointEffectNode
    }
    node_type = _substance_painter.layerstack.get_node_type(node_id)
    concrete_type = concrete_node_type.get(node_type)

    if concrete_type is None:
        raise ValueError('Unable to convert node type to node class')

    return concrete_type(node_id)


class FillParamsEditorMixin:
    """
    A mixin allowing manipulation of this fill parameters.

    :meta private:
    """

    def get_projection_mode(self) -> ProjectionMode:
        """
        Get the current projection mode.

        Returns:
            ProjectionMode: The current projection mode.
        """
        return _substance_painter.layerstack.get_projection_mode(self.uid())

    def set_projection_mode(self, projection_mode: ProjectionMode):
        """
        Switch to a new projection mode.

        Args:
            projection_mode(ProjectionMode): The new projection mode.

        Raises:
            ValueError: If the projection mode is not supported in the current context.
        """
        _substance_painter.layerstack.set_projection_mode(self.uid(), projection_mode)

    def get_projection_parameters(self) -> ProjectionParams | None:
        """
        Get the current projection parameters.
        Each kind of Projection Mode returns a specific kind of ProjectionParams, supporting a
        different set of features.
        `Fill` mode support no parameters, and returns None.

        Returns:
            ProjectionParams: The current projection parameters, or None for `Fill`.

        See also:
            :meth:`get_projection_mode`,
            `Fill projections documentation`_
        """
        proj_params = _substance_painter.layerstack.get_projection_params(self.uid())
        return _proj_params_global_to_specific(proj_params[0], proj_params[1])

    def set_projection_parameters(self, projection_parameters: ProjectionParams):
        """
        Set projection parameters and update the current projection mode accordingly.

        Args:
            projection_parameters(ProjectionParams): The new parameters to apply.

        Raises:
            ValueError: If the projection parameters are not supported in the current context.

        See also:
            :meth:`get_projection_parameters`,
            `Fill projections documentation`_
        """
        _substance_painter.layerstack.set_projection_params(
            self.uid(), _proj_mode_from_specific_params(projection_parameters),
            _proj_params_specific_to_global(projection_parameters))


class Node(ReadOnlyUid):
    """
    Abstract class to manipulate common properties of a layer stack node.
    Each node is identified by a node uid.

    Calling methods of a Node with an incorrect `uid` throws a ValueError.
    This could happen when instanciating a Node providing its `uid` by hand, or when the Node no
    longer refers to existing data in the Layer Stack.
    
    See also:
        :func:`substance_painter.layerstack.get_node_by_uid`,
        :ref:`layerstack_edition_insertion` section.
    """

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.uid() == self.uid()

    def __hash__(self):
        return hash(self.uid())

    def get_type(self) -> NodeType:
        """
        Check the type of the node.

        Returns:
            NodeType: The node type.
        """
        return _substance_painter.layerstack.get_node_type(self.uid())

    def get_texture_set(self) -> TextureSet:
        """
        Get the TextureSet this node belongs to.

        Returns:
            TextureSet: the TextureSet this node belongs to.
        """
        return TextureSet(_substance_painter.layerstack.get_texture_set(self.uid()))

    def is_visible(self) -> bool:
        """
        Check whether this node is rendered.

        Returns:
            bool: Whether this node is rendered.
        """
        return _substance_painter.layerstack.is_visible(self.uid())

    def set_visible(self, visible: bool):
        """
        Enable this node for rendering.

        Args:
            visible (bool): Whether to enable this node for rendering.
        """
        return _substance_painter.layerstack.set_visible(self.uid(), visible)

    def get_name(self) -> str:
        """
        Get the name assigned to this Node.

        Returns:
            str: The Node name.
        """
        return _substance_painter.layerstack.get_name(self.uid())

    def set_name(self, name: str):
        """
        Change this node name.

        Args:
            name (str): New name to use.
        """
        return _substance_painter.layerstack.set_name(self.uid(), name)

    def is_in_mask_stack(self) -> bool:
        """
        Check whether this node is part of a mask stack.

        Returns:
            bool: Whether this node is part of a mask stack.
        """
        return _substance_painter.layerstack.is_in_mask_stack(self.uid())

    def has_blending(self) -> bool:
        """
        Check whether this node supports blending information (blending mode + opacity).
        The blending might be per Channel Type for regular nodes, or monochannel for nodes
        inside a mask stack.

        Returns:
            bool: Whether this node supports blending information.

        See also:
            :meth:`is_in_mask_stack`,
            `Blending modes documentation`_
        """
        return _substance_painter.layerstack.has_blending(self.uid())

    def get_blending_mode(self, channel: Optional[ChannelType] = None) -> BlendingMode:
        """
        Get the blending mode for a Node.
        If the node is not in a mask stack, a Channel Type must be provided.
        If the node is in a mask stack, Channel Type must be None.

        Args:
            channel(Optional[ChannelType]): Channel Type to query or None for mask nodes.

        Returns:
            BlendingMode: The blending mode of this node for the given Channel Type or for the mask.

        Raises:
            ValueError: If the node has blending information per Channel Type and no Channel Type
                is provided, or if the node has blending information without Channel Type and a
                Channel Type is provided.

        See also:
            :meth:`is_in_mask_stack`,
            :meth:`has_blending`,
            `Blending modes documentation`_
        """
        return _substance_painter.layerstack.get_blending_mode(self.uid(), channel)

    def set_blending_mode(self, blending_mode: BlendingMode, channel: Optional[ChannelType] = None):
        """
        Set the blending mode for a Node.
        If the node is not in a mask stack, a Channel Type must be provided.
        If the node is in a mask stack, Channel Type must be None.

        Args:
            blending_mode(BlendingMode): New blending mode to apply.
            channel(Optional[ChannelType]): Channel type to update or None for mask nodes.

        Raises:
            ValueError: If the node has blending information per Channel Type and no Channel Type
                is provided, or if the node has blending information without Channel Type and a
                Channel Type is provided.

        See also:
            :meth:`is_in_mask_stack`,
            :meth:`has_blending`,
            `Blending modes documentation`_
        """
        _substance_painter.layerstack.set_blending_mode(self.uid(), blending_mode, channel)

    def get_opacity(self, channel: Optional[ChannelType] = None) -> float:
        """
        Get the opacity for a Node.
        If the node is not in a mask stack, a Channel Type must be provided.
        If the node is in a mask stack, Channel Type must be None.

        Args:
            channel(Optional[ChannelType]): Channel Type to query or None for mask nodes.

        Returns:
            float: The opacity of this node for the given Channel Type or for the mask.

        Raises:
            ValueError: If the node has blending information per Channel Type and no Channel Type
                is provided, or if the node has blending information without Channel Type and a
                Channel Type is provided.

        See also:
            :meth:`is_in_mask_stack`
            :meth:`has_blending`
        """
        return _substance_painter.layerstack.get_opacity(self.uid(), channel)

    def set_opacity(self, opacity: float, channel: Optional[ChannelType] = None):
        """
        Set the opacity for a node.
        If the node is not in a mask stack, a Channel Type must be provided.
        If the node is in a mask stack, Channel Type must be None.

        Args:
            opacity(float): New opacity to apply, value between 0.0 and 1.0.
            channel(Optional[ChannelType]): Channel Type to update or None for mask nodes.

        Raises:
            ValueError: If the node has blending information per Channel Type and no Channel Type
                is provided, or if the node has blending information without Channel Type and a
                Channel Type is provided.

        See also:
            :meth:`is_in_mask_stack`
            :meth:`has_blending`
        """
        _substance_painter.layerstack.set_opacity(self.uid(), opacity, channel)

    def get_stack(self) -> Stack:
        """
        Get the stack that contains this node.

        Returns:
            Stack: The stack that contains this node.
        """
        return Stack(_substance_painter.layerstack.get_stack(self.uid()))

    def get_parent(self) -> Node:
        """
        Get the parent of this node.

        Returns:
            Node: The parent of this node, or None if this node is a root layer.
        """
        parent_node_id = _substance_painter.layerstack.get_parent_node(self.uid())
        if parent_node_id is None:
            return None
        return _node_id_to_concrete_node(parent_node_id)

    def get_next_sibling(self) -> Node:
        """
        Get the next sibling of this node.

        Returns:
            Node: The next sibling of this node, or None if this node is the first sibling.
        """
        next_sibling_node_id = _substance_painter.layerstack.get_next_sibling_node(self.uid())
        if next_sibling_node_id is None:
            return None
        return _node_id_to_concrete_node(next_sibling_node_id)

    def get_previous_sibling(self) -> Node:
        """
        Get the previous sibling of this node.

        Returns:
            Node: The previous sibling of this node, or None if this node is the last sibling.
        """
        prev_sibling_node_id = _substance_painter.layerstack.get_previous_sibling_node(self.uid())
        if prev_sibling_node_id is None:
            return None
        return _node_id_to_concrete_node(prev_sibling_node_id)


class LayerNode(Node):
    """
    A Node that is part of the main hierarchy. Every Layer such as a paint of fill layer, as long as
    groups, are organized into this hierarchy.
    As such, you can query sub layers (in the case the LayerNode is a group), but also associate
    content effects and mask effects (such as levels and filters and so on).

    See also:
        :func:`substance_painter.layerstack.get_node_by_uid`,
        :ref:`layerstack_edition_insertion` section.
    """

    def content_effects(self) -> List[EffectNode]:
        """
        Query the content effects of this node, ordered like in the layer stack.

        Returns:
            The content effects of this node.
        """
        return [
            _node_id_to_concrete_node(node_id)
            for node_id in _substance_painter.layerstack.content_effects(self.uid())
        ]

    def mask_effects(self) -> List[EffectNode]:
        """
        Query the mask effects of this node, ordered like in the layer stack.

        Returns:
            The mask effects of this node.
        """
        return [
            _node_id_to_concrete_node(node_id)
            for node_id in _substance_painter.layerstack.mask_effects(self.uid())
        ]

    def instances(self) -> List[LayerNode]:
        """
        Return the list of instances of this layer.
        See the documentation on layer instancing if you are not familiar with the
        concept: `Layer instancing documentation`_.

        .. _Layer instancing documentation:
            https://helpx.adobe.com/substance-3d-painter/interface/layer-stack/layer-instancing.html

        Returns:
            List[LayerNode]: The instances of this node.
        """
        return [
            InstanceLayerNode(node_id)
            for node_id in _substance_painter.layerstack.instances(self.uid())
        ]

    def get_geometry_mask_type(self) -> GeometryMaskType:
        """
        Query the geometry mask type currently applied to this node.

        Returns:
            GeometryMaskType: The type of geometry mask for this layer node.

        See also:
            `Geometry mask documentation`_
        
        .. _Geometry mask documentation:
            https://helpx.adobe.com/substance-3d-painter/interface/layer-stack/geometry-mask.html

        """
        return _substance_painter.layerstack.get_geometry_mask_type(self.uid())

    def set_geometry_mask_type(self, geometry_mask_type: GeometryMaskType):
        """
        Set the geometry mask type to apply to this node.
        :class:`GeometryMaskType.UVTile <GeometryMaskType>` is only
        supported when the corresponding Texture Set uses UV Tiles.

        Args:
            geometry_mask_type(GeometryMaskType): The type of geometry mask for this layer node.

        Raises:
            ValueError: When GeometryMaskType.UVTile is requested and the project does not
                support UV Tiles.

        See also:
            :meth:`substance_painter.textureset.TextureSet.has_uv_tiles`,
            `Geometry mask documentation`_

        """
        _substance_painter.layerstack.set_geometry_mask_type(self.uid(), geometry_mask_type)

    def get_geometry_mask_enabled_meshes(self) -> List[str]:
        """
        Get the list of enabled meshes for the geometry mask. Meshes that are not in this list are
        disabled.
        To get the complete list of meshes, see
        :meth:`substance_painter.textureset.TextureSet.all_mesh_names`.

        Returns:
            List[str]: The list of enabled meshes for the geometry mask.

        See also:
            `Geometry mask documentation`_
        """
        return _substance_painter.layerstack.get_geometry_mask_enabled_meshes(self.uid())

    def set_geometry_mask_enabled_meshes(self, mesh_names: List[str]):
        """
        Set the list of enabled meshes for the geometry mask. Meshes that are not in this list will
        be disabled. To get the complete list of meshes, see
        :meth:`substance_painter.textureset.TextureSet.all_mesh_names`.

        Args:
            mesh_names(List[str]): The list of meshes to enable for the geometry mask.

        Raises:
            ValueError: If a mesh name does not belongs to this texture set.

        See also:
            `Geometry mask documentation`_
        """
        stack = self.get_stack()
        textureset = stack.material()
        all_mesh_names = set(textureset.all_mesh_names())
        invalid_mesh_names = set(mesh_names) - all_mesh_names
        if invalid_mesh_names:
            msg = f"The following set of mesh names doesn't exist: {invalid_mesh_names}"
            raise ValueError(msg)

        _substance_painter.layerstack.set_geometry_mask_enabled_meshes(self.uid(), mesh_names)

    def get_geometry_mask_enabled_uv_tiles(self) -> List[UVTile]:
        """
        Get the list of enabled UV Tiles for the geometry mask. UV Tiles that are not in this list
        are disabled. To get the complete list of UV Tiles, see
        :meth:`substance_painter.textureset.TextureSet.all_uv_tiles`.

        Returns:
            List[UVTile]: The list of enabled UV Tiles for the geometry mask.

        See also:
            `Geometry mask documentation`_
        """
        texture_set = self.get_texture_set()
        return [
            UVTile(*uv_tile, texture_set.material_id) for uv_tile in
            _substance_painter.layerstack.get_geometry_mask_enabled_uv_tiles(self.uid())
        ]

    def set_geometry_mask_enabled_uv_tiles(self, uv_tiles: List[UVTile]):
        """
        Set the list of enabled UV Tiles for the geometry mask. UV Tiles that are not in this list
        will de disabled. To get the complete list of UV Tiles, see
        :meth:`substance_painter.textureset.TextureSet.all_uv_tiles`.

        Args:
            uv_tiles(List[UVTile]): The list of UV Tiles to enable for the geometry mask.

        Raises:
            ValueError: If a UV Tile does not belong to this texture set.

        See also:
            `Geometry mask documentation`_
        """
        stack = self.get_stack()
        textureset = stack.material()
        all_uv_tiles = set(textureset.all_uv_tiles())
        invalid_uv_tiles = set(uv_tiles) - all_uv_tiles
        if invalid_uv_tiles:
            short_names = [(x.u, x.v) for x in invalid_uv_tiles]
            msg = f"The following set of UV Tiles coordinates doesn't exist: {short_names}"
            raise ValueError(msg)

        _substance_painter.layerstack.set_geometry_mask_enabled_uv_tiles(
            self.uid(), [(tile.u, tile.v) for tile in uv_tiles])

    def has_mask(self) -> bool:
        """
        Check whether this node has a mask.

        Returns:
            bool: Whether this node has a mask.
        """
        return _substance_painter.layerstack.has_mask(self.uid())

    def add_mask(self, background: MaskBackground):
        """
        Add a mask on this node with the specified background.

        Raises:
            ValueError: If a mask is already set on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        _substance_painter.layerstack.add_mask(self.uid(), background)

    def remove_mask(self):
        """
        Remove this node mask, including all its effects.

        Raises:
            ValueError: If no mask exists on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        _substance_painter.layerstack.remove_mask(self.uid())

    def get_mask_background(self) -> MaskBackground:
        """
        Query the type of mask used by this node.

        Returns:
            MaskBackground: The mask background applied to this node.

        Raises:
            ValueError: If no mask exists on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        return _substance_painter.layerstack.get_mask_background(self.uid())

    def set_mask_background(self, background: MaskBackground):
        """
        Set the mask background on this node.

        Args:
            background(MaskBackground): The mask background to be applied on this node mask.

        Raises:
            ValueError: If no mask exists on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        _substance_painter.layerstack.set_mask_background(self.uid(), background)

    def is_mask_enabled(self) -> bool:
        """
        Query whether the mask is currently enabled.

        Returns:
            bool: Whether the mask is currently enabled.

        Raises:
            ValueError: If no mask exists on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        return _substance_painter.layerstack.is_mask_enabled(self.uid())

    def enable_mask(self, enabled: bool):
        """
        Set whether the mask is currently enabled.

        Args:
            enabled(bool): Whether to enable the mask.

        Raises:
            ValueError: If no mask exists on this node.
                Use :meth:`has_mask` to check if the node has a mask.
        """
        _substance_painter.layerstack.enable_mask(self.uid(), enabled)


class GroupLayerNode(LayerNode):
    """
    A node allowing manipulation of a Group layer of the Layer Stack.
    """

    def sub_layers(self) -> List[LayerNode]:
        """
        Query sub layers of this node. Only get the direct children, ordered like in the layer
        stack.

        Returns:
            List[LayerNode]: The sub layers of this node.
        """
        return [
            _node_id_to_concrete_node(node_id)
            for node_id in _substance_painter.layerstack.sub_layers(self.uid())
        ]

    def is_collapsed(self) -> bool:
        """
        Query if the group is in collapsed state.

        Returns:
            bool: Whether this group is collapsed.
        """
        return _substance_painter.layerstack.is_collapsed(self.uid())

    def set_collapsed(self, collapsed: bool):
        """
        Set the collapsed state of the group.

        Args:
            collapsed(bool): Whether to collapse the group.
        """
        _substance_painter.layerstack.set_collapsed(self.uid(), collapsed)


class PaintLayerNode(LayerNode):
    """
    A node allowing manipulation of a Paint layer.

    Note:
        Strokes are not accessible from the Python API.
    """


class InstanceLayerNode(LayerNode):
    """
    A node allowing manipulation of an Instance layer.

    To retrieve the list of :class:`InstanceLayerNode` from the source layer,
    see :meth:`LayerNode.instances`
    """

    def instance_source(self) -> LayerNode:
        """
        Return the source layer of this instance.

        Returns:
            LayerNode: The source layer if this instance.
        """
        return _node_id_to_concrete_node(_substance_painter.layerstack.model(self.uid()))


class FillLayerNode(FillParamsEditorMixin, SourceEditorMixin, LayerNode):
    """
    A node allowing manipulation of a Fill layer.
    """


HierarchicalNode = Union[LayerNode, GroupLayerNode, PaintLayerNode, InstanceLayerNode,
                         FillLayerNode]


class GeneratorEffectNode(ActiveChannelsMixin, Node):
    """
    A node allowing manipulation of a Generator effect.
    """

    def get_source(self) -> SourceSubstance:
        """
        Get the source procedural of the generator, or None if no generator is set.

        Returns:
            SourceSubstance: The generator's source.
        """
        return substance_painter.source._from_id(  # pylint: disable = protected-access
            _substance_painter.source.get_generator_source(self.uid()))

    def set_source(self, res: substance_painter.resource.ResourceID) -> SourceSubstance:
        """
        Create and assign a source from the given resource and return the created source.
        The resource must have a :class:`Usage.GENERATOR <substance_painter.resource.Usage>` usage.

        Args:
            res(substance_painter.resource.ResourceID): The generator material to apply.

        Returns:
            SourceSubstance: The generator's source.

        Raises:
            ValueError: If `res` is not a valid resource or does not have
                :class:`Usage.GENERATOR <substance_painter.resource.Usage>` usage.
        """
        return substance_painter.source._from_id(  # pylint: disable = protected-access
            _substance_painter.source.set_generator_source(self.uid(), res.url()))

    def remove_source(self) -> None:
        """
        Remove the currently used source.
        """
        _substance_painter.source.remove_generator_source(self.uid())


class PaintEffectNode(Node):
    """
    A node allowing manipulation of a Paint effect.

    Note:
        Strokes are not accessible from the Python API.
    """


class FillEffectNode(FillParamsEditorMixin, SourceEditorMixin, Node):
    """
    A node allowing manipulation of a Fill effect.
    """


class LevelsEffectNode(Node):
    """
    A node allowing manipulation of a Levels effect.

    See also:
        `Levels effect documentation`_

    .. _Levels effect documentation:
        https://helpx.adobe.com/substance-3d-painter/features/effects/levels.html
    """

    @property
    def affected_channel(self) -> ChannelType:
        """
        The channel affected by the current level effect.

        :getter: Returns the affected channel.
        :setter: Set the affected channel.
        :type: ChannelType
        """
        return _substance_painter.layerstack.get_levels_effect_affected_channel(self.uid())

    @affected_channel.setter
    def affected_channel(self, channel: ChannelType) -> None:
        return _substance_painter.layerstack.set_levels_effect_affected_channel(self.uid(), channel)

    def get_parameters(self) -> LevelsParams:
        """
        Get the current parameters of this levels effect.

        Returns:
            LevelsParams: The current level parameters.
        """
        params = _substance_painter.layerstack.get_levels_params(self.uid())

        # Result is mono channel either if the effect is in a mask stack, either because the
        # channel is set to a monochromatic channel
        try:
            stack = self.get_stack()
            channel = stack.get_channel(self.affected_channel)
            is_color = channel.is_color()
        except ValueError:
            is_color = False

        return levels._from_private_params(params, is_color)  # pylint: disable = protected-access

    def set_parameters(self, params: LevelsParams) -> None:
        """
        Set new parameters for this levels effect.

        Args:
            params(LevelsParams): The new parameters.
        """
        private_params = levels._to_private_params(params)  # pylint: disable = protected-access
        _substance_painter.layerstack.set_levels_params(self.uid(), private_params)


@dataclasses.dataclass
class CompareMaskEffectParams:
    """
    A compare mask effect parameters.

    :param channel: The channel to compare between the source and the target to create a
        mask from. Only used when some operands refers to Layers.
    :param left_operand: The left operand of the comparison.
    :param right_operand: The right operand of the comparison.
    :param operation: The comparison operation to perform.
    :param constant: Value to compare against when some operand is
        :class:`CompareMaskEffectOperand.Constant <CompareMaskEffectOperand>`. Between 0.0 and 1.0.
    :param tolerance: Tolerance value to use when `operation` is
        :class:`CompareMaskEffectOperation.WithinTolerance <CompareMaskEffectOperand>`.
        Between 0.0 and 1.0.
    :param hardness: Controls the smoothness/hardness of the resulting mask comparison.
        Between 0.0 and 1.0.
    """
    channel: ChannelType
    left_operand: CompareMaskEffectOperand
    right_operand: CompareMaskEffectOperand
    operation: CompareMaskEffectOperation
    constant: float
    tolerance: float
    hardness: float


class CompareMaskEffectNode(Node):
    """
    A node allowing manipulation of a Compare Mask effect.

    See also:
        `Compare Mask effect documentation`_

    .. _Compare Mask effect documentation:
        https://helpx.adobe.com/substance-3d-painter/features/effects/compare-mask.html
    """

    def get_parameters(self) -> CompareMaskEffectParams:
        """
        Get the current parameters of this compare mask effect.

        Returns:
            CompareMaskEffectParams: The current parameters of this compare mask effect.
        """
        params = _substance_painter.layerstack.get_compare_mask_params(self.uid())
        return CompareMaskEffectParams(params.channel, params.left_operand, params.right_operand,
                                       params.operation, params.constant, params.tolerance,
                                       params.hardness)

    def set_parameters(self, params: CompareMaskEffectParams) -> None:
        """
        Set new parameters of this compare mask effect.

        Args:
            params(CompareMaskEffectParams): The new parameters.
        """
        private_params = _substance_painter.layerstack.CompareMaskEffectParams()
        private_params.channel = params.channel
        private_params.left_operand = params.left_operand
        private_params.right_operand = params.right_operand
        private_params.operation = params.operation
        private_params.tolerance = params.tolerance
        private_params.constant = params.constant
        private_params.hardness = params.hardness
        _substance_painter.layerstack.set_compare_mask_params(self.uid(), private_params)


class FilterEffectNode(ActiveChannelsMixin, Node):
    """
    A node allowing manipulation of a Filter effect.
    """

    def get_source(self) -> SourceSubstance:
        """
        Get the source procedural of the filter, or None if no filter is set.

        Returns:
            SourceSubstance: The filter's source.
        """
        return substance_painter.source._from_id(  # pylint: disable = protected-access
            _substance_painter.source.get_filter_source(self.uid()))

    def set_source(self, res: substance_painter.resource.ResourceID) -> SourceSubstance:
        """
        Create and assign a source from the given resource and return the created source.
        The resource must have a :class:`Usage.FILTER <substance_painter.resource.Usage>` usage.

        Args:
            res(substance_painter.resource.ResourceID): The filter material to apply.

        Returns:
            SourceSubstance: The filter's source.

        Raises:
            ValueError: If `res` is not a valid resource or does not have
                :class:`Usage.FILTER <substance_painter.resource.Usage>` usage.
        """
        return substance_painter.source._from_id(  # pylint: disable = protected-access
            _substance_painter.source.set_filter_source(self.uid(), res.url()))

    def remove_source(self) -> None:
        """
        Remove the currently used source.
        """
        _substance_painter.source.remove_filter_source(self.uid())


@dataclasses.dataclass
class ColorSelectionEffectParams:
    """
    A color selection effect parameters.

    :param id_mask: Which color map to use.
        Typically the ID Mask baked map. Must have
        :class:`Usage.TEXTURE <substance_painter.resource.Usage>` and be part of the project.
    :param output_value: Output value when selection matches. Between 0.0 and 1.0.
    :param hardness: Hardness of the selection. Between 0.0 and 1.0.
    :param tolerance: Tolerance of the selection. Between 0.0 and 1.0.
    :param background_color: Output value when selection does not match.
    :param colors: List of colors to match in the id_mask.
    """

    id_mask: Optional[substance_painter.resource.ResourceID]
    output_value: float
    hardness: float
    tolerance: float
    background_color: ColorSelectionBackgroundColor
    colors: List[Color]


class ColorSelectionEffectNode(Node):
    """
    A node allowing manipulation of a Color Selection effect.
    """

    def get_parameters(self) -> ColorSelectionEffectParams:
        """
        Get the current parameters of this color selection effect.

        Returns:
            ColorSelectionEffectParams: The current parameters of this color selection effect.
        """
        private_params = _substance_painter.layerstack.get_color_selection_params(self.uid())
        id_mask = substance_painter.resource.ResourceID.from_url(
            private_params.id_mask) if private_params.id_mask else None
        colors = [_to_public_color(v) for v in private_params.colors]
        return ColorSelectionEffectParams(id_mask, private_params.output_value,
                                          private_params.hardness, private_params.tolerance,
                                          private_params.background_color, colors)

    def set_parameters(self, params: ColorSelectionEffectParams) -> None:
        """
        Set new parameters of this compare mask effect.

        Args:
            params(ColorSelectionEffectParams): The new parameters.

        Raises:
            ResourceNotFoundError: If the resource ``params.id_mask`` is not found or is not of
                :class:`Type.IMAGE <substance_painter.resource.Type>`.
        """
        private_params = _substance_painter.layerstack.ColorSelectionEffectParams()
        private_params.id_mask = params.id_mask.url() if params.id_mask else ''
        private_params.output_value = params.output_value
        private_params.hardness = params.hardness
        private_params.tolerance = params.tolerance
        private_params.background_color = params.background_color
        private_params.colors = [_to_private_color(v) for v in params.colors]
        _substance_painter.layerstack.set_color_selection_params(self.uid(), private_params)


class AnchorPointEffectNode(Node):
    """
    A node allowing manipulation of an Anchor Point effect.
    """


EffectNode = Union[GeneratorEffectNode, PaintEffectNode, FillEffectNode, LevelsEffectNode,
                   CompareMaskEffectNode, FilterEffectNode, ColorSelectionEffectNode,
                   AnchorPointEffectNode]


def get_root_layer_nodes(stack: Stack) -> List[HierarchicalNode]:
    """
    Get the root layers of a stack, ordered like in the layer stack.

    Args:
        stack(Stack): Stack to query.

    Raises:
        ValueError: If `stack` is invalid.

    Returns:
        The root layers of the stack.
    """
    return [
        _node_id_to_concrete_node(node_id)
        for node_id in _substance_painter.layerstack.get_root_layers_from_stack(stack.stack_id)
    ]


def get_node_by_uid(node_id: int) -> List[Union[HierarchicalNode, EffectNode]]:
    """
    Get a node by its internal identifier.

    Args:
        node_id(int): The node uid.

    Raises:
        ValueError: If the given uid doesn't correspond to a valid node.

    Returns:
        The node with the given uid.
    """
    return _node_id_to_concrete_node(node_id)


def get_selected_nodes(stack: Stack) -> List[Union[HierarchicalNode, EffectNode]]:
    """
    Get the selected nodes of a Stack, ordered like in the layer stack.

    Args:
        stack(Stack): Stack to query.

    Returns:
        The selected nodes of the stack.
    """
    return [
        _node_id_to_concrete_node(node_id)
        for node_id in _substance_painter.layerstack.get_selected_nodes_from_stack(stack.stack_id)
    ]


def set_selected_nodes(nodes: List[EffectNode] | List[LayerNode]):
    """
    Select the given nodes in the layer stack UI.

    Args:
        nodes: Nodes to select.

    Raises:
        ValueError: If the nodes doesn't belong to the currently selected texture set.
        RuntimeError: If called from a :class:`ScopedModification` section
    """
    node_ids = [node.uid() for node in nodes]
    _substance_painter.layerstack.select_nodes(node_ids)



def get_selection_type(layer: LayerNode) -> SelectionType:
    """
    Return which part of a layer is selected (content, mask, etc...).

    Args:
        layer: Layer to query.

    Returns:
        SelectionType: The part of the layer that is selected.

    Raises:
        ValueError: If the layer doesn't belong to the currently selected texture set.
    """
    return _substance_painter.layerstack.get_selection_type(layer.uid())


def set_selection_type(layer: LayerNode, layer_selection_type: SelectionType):
    """
    Select which part of the layer you want to select.

    Args:
        layer: Layer to select.
        layer_selection_type: Part of the layer you want to select (content, mask, etc...).

    Raises:
        ValueError: If the layer doesn't belong to the currently selected texture set.
        RuntimeError: If called from a :class:`ScopedModification` section
    """
    _substance_painter.layerstack.set_selection_type(layer.uid(), layer_selection_type)


def delete_node(node: Node):
    """
    Delete the given node.

    Args:
        node(Node): Node to delete.
    """
    _substance_painter.layerstack.delete_node(node.uid())


@dataclasses.dataclass
class UVTransformationParams:
    """
    UV projection transformation parameters.

    :param scale_mode: How `scale` should be interpreted.
        For a :class:`ProjectionMode.Spherical <ProjectionMode>` projection,
        only :class:`ScaleMode.Factors <ScaleMode>` is supported.
        Using :class:`ScaleMode.MaterialPhysicalSize <ScaleMode>` is only possible when
        applied to a resource with physical size information.
    :param scale: The u/v stretch applied to the texture.
        When `scale_mode` is :class:`ScaleMode.Factors <ScaleMode>`,
        use plain factor for stretching.
        When `scale_mode` is :class:`ScaleMode.MaterialPhysicalSize <ScaleMode>`, scale must be None
        and the value will be forced to the actual material physical size.
        When `scale_mode` is :class:`ScaleMode.CustomPhysicalSize <ScaleMode>`, then scale is
        expressed in centimeters and overrides the size defined by the material
        (useful when material has no physical size information).
    :param rotation: Rotation applied to the texture.
    :param offset: Offset applied to the texture.
        The offset is unavailable for a :class:`ProjectionMode.Triplanar <ProjectionMode>`
        projection.
    """
    scale_mode: ScaleMode = None
    scale: List[float] = None
    rotation: float = None
    offset: List[float] = None


@dataclasses.dataclass
class Projection3DParams:
    """
    3D projection transformation parameters.

    :param offset: 3D offset.
    :param rotation: 3D rotation.
    :param scale: 3D scale.
        Z scaling is unavalaible when projection mode is
        :class:`ProjectionMode.Planar <ProjectionMode>` and depth culling is disabled.
    """
    offset: List[float] = None
    rotation: List[float] = None
    scale: List[float] = None


@dataclasses.dataclass
class ProjectionCullingParams:
    """
    Projection culling parameters.
    Either a depth culling or a backface culling.

    :param enabled: Whether the culling is enabled or not.
    :param hardness: Hardness of the culling, between 0 and 1.
    """
    enabled: bool = None
    hardness: float = None


@dataclasses.dataclass
class UVProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.UV <ProjectionMode>`.
    For a complete description of the parameters, see
    `UV Projection documentation`_.

    .. _UV Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/uv-projection.html

    :param filtering_mode: How to filter the image.
    :param uv_wrapping: UV Wrapping behaviour.
    :param uv_transformation: UV transformation.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)


@dataclasses.dataclass
class TriplanarProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.Triplanar <ProjectionMode>`.
    For a complete description of the parameters, see
    `Triplanar Projection documentation`_.

    .. _Triplanar Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/tri-planar-projection.html

    :param filtering_mode: How to filter the image.
    :param shape_crop_mode: How the fill is cropped.
    :param hardness: How hard is the transition between planes of the projection.
    :param uv_transformation: UV transformation.
    :param projection_3d: 3D projection.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    shape_crop_mode: ShapeCropMode = None
    hardness: float = None
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)
    projection_3d: Projection3DParams = dataclasses.field(default_factory=Projection3DParams)


#pylint: disable = too-many-instance-attributes
@dataclasses.dataclass
class PlanarProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.Planar <ProjectionMode>`.
    For a complete description of the parameters, see
    `Planar Projection documentation`_.

    .. _Planar Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/planar-projection.html

    :param filtering_mode: How to filter the image.
    :param uv_wrapping_mode: UV Wrapping behaviour.
    :param shape_crop_mode: How the fill is cropped.
    :param depth_culling: Depth culling settings.
    :param backface_culling: Backface culling settings.
    :param backface_culling_angle: Minimum angle which determines when faces that are looking
        away should be ignored, between 45 and 135.
    :param uv_transformation: UV transformation.
    :param projection_3d: 3D projection.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    shape_crop_mode: ShapeCropMode = None
    depth_culling: ProjectionCullingParams = dataclasses.field(
        default_factory=ProjectionCullingParams)
    backface_culling: ProjectionCullingParams = dataclasses.field(
        default_factory=ProjectionCullingParams)
    backface_culling_angle: float = None
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)
    projection_3d: Projection3DParams = dataclasses.field(default_factory=Projection3DParams)


@dataclasses.dataclass
class WarpProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.Warp <ProjectionMode>`.
    For a complete description of the parameters, see
    `Warp Projection documentation`_.

    .. _Warp Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/warp-projection.html

    :param filtering_mode: How to filter the image.
    :param uv_wrapping_mode: UV Wrapping behaviour.
    :param shape_crop_mode: How the fill is cropped.
    :param projection_depth: How far the projection goes along its Z axis.
    :param depth_culling: Depth culling parameters.
    :param uv_transformation: UV transformation.
    :param projection_3d: 3D projection.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    shape_crop_mode: ShapeCropMode = None
    projection_depth: float = None
    depth_culling: ProjectionCullingParams = dataclasses.field(
        default_factory=ProjectionCullingParams)
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)
    projection_3d: Projection3DParams = dataclasses.field(default_factory=Projection3DParams)


@dataclasses.dataclass
class SphericalProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.Spherical <ProjectionMode>`.
    For a complete description of the parameters, see
    `Spherical Projection documentation`_.

    .. _Spherical Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/spherical-projection.html

    :param filtering_mode: How to filter the image.
    :param uv_wrapping_mode: UV Wrapping behaviour.
    :param shape_crop_mode: How the fill is cropped.
    :param uv_transformation: UV transformation.
        Spherical projection do not support UV transformation physical size options.
    :param projection_3d: 3D projection.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    shape_crop_mode: ShapeCropMode = None
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)
    projection_3d: Projection3DParams = dataclasses.field(default_factory=Projection3DParams)


@dataclasses.dataclass
class CylindricalProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.Cylindrical <ProjectionMode>`.
    For a complete description of the parameters, see
    `Cylindrical Projection documentation`_.

    .. _Cylindrical Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/cylindrical-projection.html

    :param filtering_mode: How to filter the image.
    :param uv_wrapping_mode: UV Wrapping behaviour.
    :param shape_crop_mode: How the fill is cropped.
    :param angle: Size of the projection on the perimeter of the cylinder.
    :param backface_culling: Backface culling parameters.
    :param uv_transformation: UV transformation.
    :param projection_3d: 3D projection.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    shape_crop_mode: ShapeCropMode = None
    angle: float = None
    backface_culling: ProjectionCullingParams = dataclasses.field(
        default_factory=ProjectionCullingParams)
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)
    projection_3d: Projection3DParams = dataclasses.field(default_factory=Projection3DParams)

    _flatten_overrides_: ClassVar[Dict[str, str]] = {
        'backface_culling_enabled': 'cylinder_hide_caps'
    }


@dataclasses.dataclass
class UVSetToUVSetProjectionParams:
    """
    Parameters that control the fill behaviour when the projection mode is
    :class:`ProjectionMode.UVSetToUVSet <ProjectionMode>`.
    For a complete description of the parameters, see
    `UVSetToUVSet Projection documentation`_.

    .. _UVSetToUVSet Projection documentation:
        https://helpx.adobe.com/substance-3d-painter/painting/fill-projections/uv-set-to-uv-set-projection.html

    :param source_uv_set: Mesh UV set index used as projection source (0: no effect).
    :param filtering_mode: How to filter the image.
    :param uv_wrapping: UV Wrapping behaviour.
    :param uv_transformation: UV transformation.

    See also:
        :meth:`FillLayerNode.get_projection_mode`
        :meth:`FillLayerNode.get_projection_parameters`
    """
    source_uv_set: int = None
    filtering_mode: FilteringMode = None
    uv_wrapping_mode: UVWrapMode = None
    uv_transformation: UVTransformationParams = dataclasses.field(
        default_factory=UVTransformationParams)


ProjectionParams = Union[UVProjectionParams, TriplanarProjectionParams, PlanarProjectionParams,
                         WarpProjectionParams, SphericalProjectionParams,
                         CylindricalProjectionParams, UVSetToUVSetProjectionParams]
"""
Each Projection Mode has its own projection parameters.
`ProjectionParams` is used to regroup them.
"""


@dataclasses.dataclass(frozen=True)
class InsertPosition:
    """
    :class:`InsertPosition` is the object used by all the insert methods to express
    where you want the insertion to happen in the layer stack hierarchy.

    Create instances using the appropriate static methods depending on what
    you want to do. See the following examples.

    Example:
        ::

            import substance_painter as sp

            # Insert at the top of the given textureset layer stack
            insert_position = sp.layerstack.InsertPosition.from_textureset_stack(
                sp.textureset.get_active_stack())
            new_layer = sp.layerstack.insert_fill(insert_position)
            new_layer.set_name("First layer")

            # Insert a layer above new_layer
            insert_position = sp.layerstack.InsertPosition.above_node(new_layer)
            sp.layerstack.insert_fill(insert_position)

            # Insert an effect in the content stack of new_layer
            insert_position = sp.layerstack.InsertPosition.inside_node(
                new_layer, sp.layerstack.NodeStack.Content)
            new_effect = sp.layerstack.insert_fill(insert_position)
            new_effect.set_name("First effect")

            # Insert an effect below new_effect
            insert_position = sp.layerstack.InsertPosition.below_node(new_effect)
            sp.layerstack.insert_fill(insert_position)
    """
    node_id: int
    node_stack: Optional[int]

    @staticmethod
    def from_textureset_stack(stack: substance_painter.textureset.Stack) -> InsertPosition:
        """
        Generate an :class:`InsertPosition` on the top of a stack.

        Only a :class:`LayerNode` can be inserted at the top of the stack.
        For more details, see :ref:`insertion_rules_layer`.

        Args:
            stack (substance_painter.textureset.Stack): Stack in which you wish to insert.
        """
        return InsertPosition(_substance_painter.layerstack.get_stack_node_id(stack.stack_id), None)

    @staticmethod
    def above_node(node: Node) -> InsertPosition:
        """
        Generate an :class:`InsertPosition` to insert above the given node.

        Only a :class:`LayerNode` can be inserted above a :class:`LayerNode`.
        Only an :class:`EffectNode` can be inserted above an :class:`EffectNode`.
        For more details, see :ref:`insertion_rules_layer` and :ref:`insertion_rules_effect`.

        Args:
            node (Node): the node.
        """
        return InsertPosition(node.uid(),
                              _substance_painter.layerstack.InsertPositionLocation.Above)

    @staticmethod
    def below_node(node: Node) -> InsertPosition:
        """
        Generate an :class:`InsertPosition` to insert below the given node.

        Only a :class:`LayerNode` can be inserted above a :class:`LayerNode`.
        Only an :class:`EffectNode` can be inserted above an :class:`EffectNode`.
        For more details, see :ref:`insertion_rules_layer` and :ref:`insertion_rules_effect`.

        Args:
            node (Node): the node.
        """
        return InsertPosition(node.uid(),
                              _substance_painter.layerstack.InsertPositionLocation.Below)

    @staticmethod
    def inside_node(node: Node, node_stack: NodeStack) -> InsertPosition:
        """
        Generate an :class:`InsertPosition` to insert inside the given stack of a node.

        Only a :class:`LayerNode` can be inserted inside a :class:`GroupLayerNode` if `node_stack`
        is :class:`NodeStack.Substack <NodeStack>`.
        Only an :class:`EffectNode` can be inserted inside a :class:`LayerNode` if `node_stack`
        is :class:`NodeStack.Content <NodeStack>` or :class:`NodeStack.Mask <NodeStack>`.
        For more details, see :ref:`insertion_rules_layer` and :ref:`insertion_rules_effect`.

        Args:
            node (Node): the node.
            node_stack (NodeStack): indicate in which layer's stack you want
                to insert (Only valid for nodes which are layers).
        """
        internal_node_location = {
            NodeStack.Substack: _substance_painter.layerstack.InsertPositionLocation.Substack,
            NodeStack.Content: _substance_painter.layerstack.InsertPositionLocation.Content,
            NodeStack.Mask: _substance_painter.layerstack.InsertPositionLocation.Mask,
        }
        return InsertPosition(node.uid(), internal_node_location[node_stack])


def _proj_mode_from_specific_params(specific_params: ProjectionParams) -> ProjectionMode:
    specific_projection_modes = {
        UVProjectionParams: ProjectionMode.UV,
        TriplanarProjectionParams: ProjectionMode.Triplanar,
        PlanarProjectionParams: ProjectionMode.Planar,
        SphericalProjectionParams: ProjectionMode.Spherical,
        CylindricalProjectionParams: ProjectionMode.Cylindrical,
        WarpProjectionParams: ProjectionMode.Warp,
        UVSetToUVSetProjectionParams: ProjectionMode.UVSetToUVSet
    }

    return specific_projection_modes.get(type(specific_params))


def _proj_params_global_to_specific(
        proj_mode: ProjectionMode,
        global_params: _substance_painter.layerstack.FillProjectionParams) -> ProjectionParams:
    specific_params_types = {
        ProjectionMode.UV: UVProjectionParams,
        ProjectionMode.Triplanar: TriplanarProjectionParams,
        ProjectionMode.Planar: PlanarProjectionParams,
        ProjectionMode.Spherical: SphericalProjectionParams,
        ProjectionMode.Cylindrical: CylindricalProjectionParams,
        ProjectionMode.Warp: WarpProjectionParams,
        ProjectionMode.UVSetToUVSet: UVSetToUVSetProjectionParams
    }

    specific_params_type = specific_params_types.get(proj_mode)
    if specific_params_type is None:
        return None

    overrides = getattr(specific_params_type, '_flatten_overrides_', None)
    specific_params = specific_params_type()
    _utility.unflatten_attributes(global_params, specific_params, overrides)
    return specific_params


def _proj_params_specific_to_global(
        specific_params: ProjectionParams) -> _substance_painter.layerstack.FillProjectionParams:
    overrides = getattr(type(specific_params), '_flatten_overrides_', None)
    global_params = _substance_painter.layerstack.FillProjectionParams()
    _utility.flatten_attributes(specific_params, global_params, overrides)
    return global_params


def insert_fill(position: InsertPosition) -> Union[FillLayerNode, FillEffectNode]:
    """
    Insert a Fill effect or layer (depending on the insert position).

    Args:
        position(InsertPosition): Insert position.

    Returns:
        Union[FillLayerNode, FillEffectNode]: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return _node_id_to_concrete_node(
        _substance_painter.layerstack.insert_fill(dataclasses.astuple(position)))


def insert_paint(position: InsertPosition) -> Union[PaintLayerNode, PaintEffectNode]:
    """
    Insert a Paint effect or layer (depending on the insert position).

    Args:
        position(InsertPosition): Insert position.

    Returns:
        Union[PaintLayerNode, PaintEffectNode]: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return _node_id_to_concrete_node(
        _substance_painter.layerstack.insert_paint(dataclasses.astuple(position)))


def insert_group(position: InsertPosition) -> GroupLayerNode:
    """
    Insert a group layer.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`GroupLayerNode` with :class:`NodeStack.Substack <NodeStack>`
            or above/below a :class:`LayerNode`.

    Returns:
        GroupLayerNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return GroupLayerNode(_substance_painter.layerstack.insert_group(dataclasses.astuple(position)))


def instantiate(position: InsertPosition, layer: LayerNode) -> InstanceLayerNode:
    """
    Instantiate the given layer.
    See the documentation on layer instancing if you are not familiar with the
    concept: `Layer instancing documentation`_.

    .. _Layer instancing documentation:
        https://helpx.adobe.com/substance-3d-painter/interface/layer-stack/layer-instancing.html

    Args:
        position(InsertPosition): Insert position.
        layer(LayerNode): Layer to instantiate.

    Returns:
        InstanceLayerNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return InstanceLayerNode(
        _substance_painter.layerstack.instantiate(dataclasses.astuple(position), layer.uid()))


def insert_levels_effect(position: InsertPosition) -> LevelsEffectNode:
    """
    Insert a levels effect with default parameters.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Content <NodeStack>`
            or :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode`.

    Returns:
        LevelsEffectNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return LevelsEffectNode(
        _substance_painter.layerstack.insert_levels_effect(dataclasses.astuple(position)))


def insert_compare_mask_effect(position: InsertPosition) -> CompareMaskEffectNode:
    """
    Insert a compare mask effect with default parameters.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode` in the mask stack.

    Returns:
        CompareMaskEffectNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return CompareMaskEffectNode(
        _substance_painter.layerstack.insert_compare_mask_effect(dataclasses.astuple(position)))


def insert_filter_effect(
        position: InsertPosition,
        filter_substance: Optional[substance_painter.resource.ResourceID] = None
) -> FilterEffectNode:
    """
    Insert a filter effect, either empty or with the given filter resource.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Content <NodeStack>`
            or :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode`.
        filter_substance(Optional[substance_painter.resource.ResourceID]): Resource to use as
            filter. The resource must have a
            :class:`Usage.FILTER <substance_painter.resource.Usage>` usage.

    Returns:
        FilterEffectNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
        ValueError: If `filter_substance` is not a valid resource or
            does not have :class:`Usage.FILTER <substance_painter.resource.Usage>` usage.
    """
    return FilterEffectNode(
        _substance_painter.layerstack.insert_filter_effect(
            dataclasses.astuple(position),
            filter_substance.url() if filter_substance else ''))


def insert_generator_effect(
    position: InsertPosition,
    generator_substance: Optional[substance_painter.resource.ResourceID] = None
) -> GeneratorEffectNode:
    """
    Insert a Generator effect, either empty or with the given filter resource.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Content <NodeStack>` or
            :class:`NodeStack.Mask <NodeStack>` or above/below an :class:`EffectNode`.
        generator_substance(Optional[substance_painter.resource.ResourceID]): Resource to use as
            generator. The resource must have a
            :class:`Usage.GENERATOR <substance_painter.resource.Usage>` usage.

    Returns:
        GeneratorEffectNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
        ValueError: If `generator_substance` is not a valid resource or
            does not have :class:`Usage.GENERATOR <substance_painter.resource.Usage>` usage.
    """
    return GeneratorEffectNode(
        _substance_painter.layerstack.insert_generator_effect(
            dataclasses.astuple(position),
            generator_substance.url() if generator_substance else ''))


def insert_anchor_point_effect(position: InsertPosition, name: str) -> AnchorPointEffectNode:
    """
    Insert an anchor point effect.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Content <NodeStack>`
            or :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode`.
        name(str): Name of the anchor point.

    Returns:
        AnchorPointEffectNode: The new anchor point.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return AnchorPointEffectNode(
        _substance_painter.layerstack.insert_anchor_point_effect(dataclasses.astuple(position),
                                                                 name))


def insert_color_selection_effect(position: InsertPosition) -> ColorSelectionEffectNode:
    """
    Insert a color selection effect.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode` in the mask stack.

    Returns:
        ColorSelectionEffectNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
    """
    return ColorSelectionEffectNode(
        _substance_painter.layerstack.insert_color_selection_effect(dataclasses.astuple(position)))


def insert_smart_material(position: InsertPosition,
                          smart_material: substance_painter.resource.ResourceID) -> GroupLayerNode:
    """
    Insert a smart material at the given position.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`GroupLayerNode` with :class:`NodeStack.Substack <NodeStack>`
            or above/below a :class:`LayerNode`.
        smart_material(substance_painter.resource.ResourceID): The smart material to instantiate.
            The resource must have a
            :class:`Usage.SMART_MATERIAL <substance_painter.resource.Usage>` usage.

    Returns:
        GroupLayerNode: The inserted node.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
        ValueError: If `smart_material` is not a valid resource or does not have
            :class:`Usage.SMART_MATERIAL <substance_painter.resource.Usage>` usage.
    """
    return GroupLayerNode(
        _substance_painter.layerstack.insert_smart_material(dataclasses.astuple(position),
                                                            smart_material.url()))


def create_smart_material(group: GroupLayerNode, name: str) -> substance_painter.resource.Resource:
    """
    Create a smart material with name ``name`` from the given ``group``.

    :param group: The root folder of the smart material.
    :param name: The name of the smart material.
    :returns: The created smart material as a resource.
    """
    handle = _substance_painter.layerstack.create_smart_material(group.uid(), name)
    return substance_painter.resource.Resource(handle)


def insert_smart_mask(position: InsertPosition,
                      smart_mask: substance_painter.resource.ResourceID) -> List[EffectNode]:
    """
    Insert a smart mask in a mask stack.

    Args:
        position(InsertPosition): The insert position must be either inside
            a :class:`LayerNode` with :class:`NodeStack.Mask <NodeStack>`
            or above/below an :class:`EffectNode` in the mask stack.
        smart_mask(substance_painter.resource.ResourceID): The smart mask to instantiate.
            The resource must have a
            :class:`Usage.SMART_MASK <substance_painter.resource.Usage>` usage.

    Returns:
        List[EffectNode]: The inserted nodes.

    Raises:
        ValueError: If insertion failed due to an invalid `position`. See :class:`InsertPosition`.
        ValueError: If `smart_mask` is not a valid resource or does not have
            :class:`Usage.SMART_MASK <substance_painter.resource.Usage>` usage.
    """
    return [
        _node_id_to_concrete_node(node_id)
        for node_id in _substance_painter.layerstack.insert_smart_mask(
            dataclasses.astuple(position), smart_mask.url())
    ]


def create_smart_mask(layer: LayerNode, name: str) -> substance_painter.resource.Resource:
    """
    Create a smart mask with name ``name`` from the mask stack of the given ``layer``.

    :param layer: The parent layer of the mask stack to create.
    :param name: The name of the smart mask.
    :returns: The created smart mask as a resource.
    """
    handle = _substance_painter.layerstack.create_smart_mask(layer.uid(), name)
    return substance_painter.resource.Resource(handle)
