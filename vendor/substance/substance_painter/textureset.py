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
The ``textureset`` module allows to manipulate the stacks and Texture Sets of
the currently opened project.

A Texture Set has a resolution and one or more stacks, depending on whether the
material is layered or not. If the material is layered, the Texture Set has
several stacks. A stack contains one or more channels, corresponding to the
different types that the material can have (BaseColor, Specular, Roughness,
etc.). There can be only one channel of each type.
A Texture Set may also have UV Tiles.

This module exposes the corresponding :class:`TextureSet`, :class:`Stack`,
:class:`Channel and :class:`UVTile` classes, allowing to retrieve and set information
of the paintable stacks and the Texture Sets of the project, as well as their storage
format.

:func:`substance_painter.layerstack.get_root_layer_nodes` is the entry point for querying
the corresponding layer stack.

For instance, it is possible to change the channels of the stacks, or set the
resolution of the Texture Sets.

Example:
    ::

        import substance_painter.textureset

        # Show the resolution of the current Texture Set:
        active_stack = substance_painter.textureset.get_active_stack()
        material_resolution = active_stack.material().get_resolution()
        print("Resolution: {0}x{1}".format(material_resolution.width, material_resolution.height))

        # Change the resolution of the current Texture Set:
        new_resolution = substance_painter.textureset.Resolution(512, 512)
        active_stack.material().set_resolution(new_resolution)

        # Change the resolution of all Texture Sets:
        all_texture_sets = substance_painter.textureset.all_texture_sets()
        substance_painter.textureset.set_resolutions(all_texture_sets, new_resolution)

        # List all the Texture Sets:
        for texture_set in substance_painter.textureset.all_texture_sets():
            print("Texture Set '{0}': {1}".format(texture_set.name(),
                "layered" if texture_set.is_layered_material() else "not layered"))

            # Get all uv tiles in the first row
            row0 = [uvtile for uvtile in textureset.all_uv_tiles() if uvtile.v == 0]

            # Set their resolution to 2k
            new_resolution = substance_painter.textureset.Resolution(2048, 2048)
            resolutions = {uvtile:new_resolution for uvtile in row0}
            textureset.set_uvtiles_resolution(resolutions)

            # Set 1001 in 4k if its width is not high enough
            uvtile_1001 = next((uvtile for uvtile in row0 if uvtile.u == 0), None)
            new_resolution = substance_painter.textureset.Resolution(4096, 4096)
            if uvtile_1001.get_resolution().width < new_resolution.width:
                uvtile_1001.set_resolution(new_resolution)

            # Reset all uv tiles resolution:
            all_uv_tiles = texture_set.all_uv_tiles()
            texture_set.reset_uvtiles_resolution(all_uv_tiles)

        # List all the stacks of the current Texture Set:
        for stack in active_stack.material().all_stacks():
            if stack.name():
                print("Stack '{0}'".format(stack.name()))
            else:
                print("Stack has no name")

        # Find a stack called "Mask1" and set it as active:
        mask_stack = substance_painter.textureset.Stack.from_name("DefaultMaterial", "Mask1")
        if mask_stack != None:
            substance_painter.textureset.set_active_stack(mask_stack)

        # Show the current active stack:
        print(substance_painter.textureset.get_active_stack())

See also:
    :class:`Stack`,
    :class:`TextureSet`,
    :class:`UVTile`,
    `Texture Set documentation`_.
    `UV Tiles documentation`_.

.. _Texture Set documentation:
    https://www.adobe.com/go/painter-texture-set

.. _UV Tiles documentation:
    https://www.adobe.com/go/painter-uv-tiles
"""

import dataclasses
import typing
import substance_painter.resource
import _substance_painter.textureset
from . import _utility

ChannelFormat = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.textureset.ChannelFormat, __name__)
"""The texture format of a channel.

Members:

================= =========== ====================== =================== =========
Name              Type        Dynamic range          Bits per component  Storage
================= =========== ====================== =================== =========
``sRGB8``         Color       normalized fixed point  8                  sRGB
``L8``            Grayscale   normalized fixed point  8                  linear
``RGB8``          Color       normalized fixed point  8                  linear
``L16``           Grayscale   normalized fixed point 16                  linear
``RGB16``         Color       normalized fixed point 16                  linear
``L16F``          Grayscale   HDR floating point     16                  linear
``RGB16F``        Color       HDR floating point     16                  linear
``L32F``          Grayscale   HDR floating point     32                  linear
``RGB32F``        Color       HDR floating point     32                  linear
================= =========== ====================== =================== =========
"""

ChannelType = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.textureset.ChannelType, __name__)
"""All possible types of channel in a document.
To get the actual list of channel types in use for a particular Stack, call
:meth:`substance_painter.textureset.Stack.all_channels`.

Members:

``BaseColor``, ``Height``, ``Specular``, ``SpecularEdgeColor``, ``Opacity``,
``Emissive``, ``Displacement``, ``Glossiness``, ``Roughness``,
``Anisotropylevel``, ``Anisotropyangle``, ``Transmissive``, ``Reflection``,
``Ior``, ``Metallic``, ``Normal``, ``AO``, ``Diffuse``, ``Specularlevel``,
``BlendingMask``, ``Translucency``, ``Scattering``, ``ScatterColor``,
``SheenOpacity``, ``SheenRoughness``, ``SheenColor``, ``CoatOpacity``,
``CoatColor``, ``CoatRoughness``, ``CoatSpecularLevel``, ``CoatNormal``,
``User0``, ``User1``, ``User2``, ``User3``, ``User4``, ``User5``, ``User6``,
``User7``, ``User8``, ``User9``, ``User10``, ``User11``, ``User12``, ``User13``,
``User14``, ``User15``
"""

MeshMapUsage = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.textureset.MeshMapUsage, __name__)
"""
Members:

``AO``, ``BentNormals``, ``Curvature``, ``Height``, ``ID``, ``Normal``,
``Opacity``, ``Position``, ``Thickness``, ``WorldSpaceNormal``
"""


@dataclasses.dataclass
class Resolution:
    """
    Two dimensional resolution.

    For Texture Sets and UV Tiles, there are restrictions. The resolution must
    be a power of 2, for example 256, 512, 1024, 2048, etc.
    It must also be within the range of accepted resolutions.

    For UV Tiles, resolution must be square (ie width = height).

    :param width: The width in pixels.
    :param height: The height in pixels.

    See also:
        :meth:`TextureSet.get_resolution`,
        :meth:`TextureSet.set_resolution`,
        :meth:`UVTile.get_resolution`,
        :meth:`UVTile.set_resolution`,
        :func:`set_resolutions`.
    """
    width: int = 1024
    height: int = 1024


@dataclasses.dataclass(frozen=True)
class Channel:
    """A `Substance 3D Painter` channel.

    A channel can be one of the predefined types (`BaseColor`, `Specular`, `Roughness`,
    etc.) or a user defined type (`User0` to `User7`), corresponding to the material.
    The channel belongs to a stack. The stack can have one or more of them, but it
    can have only one channel of each :class:`ChannelType`.


    Example:
        ::

            import substance_painter.textureset

            # Get the unnamed stack of "TextureSetName":
            paintable_stack = substance_painter.textureset.Stack.from_name("TextureSetName")

            # Get the channel "BaseColor" of that stack:
            base_color_channel = paintable_stack.get_channel(
                substance_painter.textureset.ChannelType.BaseColor)

            # Print the color format and bit depth of the base color channel:
            print("The channel format uses {0} {1}.".format(
                "RGB" if base_color_channel.is_color() else "L",
                base_color_channel.bit_depth()))

            # Change the format and bit depth of the base color channel:
            base_color_channel.edit(
                channel_format = substance_painter.textureset.ChannelFormat.RGB16)
    """
    channel_id: int = None

    def format(self) -> ChannelFormat:
        """
        Get the channel format. The format indicates both if the channel is color
        or grayscale, its dynamic range, its bits per component, and if the storage
        is linear or sRGB.

        Returns:
            ChannelFormat: This channel format.
        """
        return _substance_painter.textureset.channel_format(self.channel_id)

    def label(self) -> str:
        """
        Get the user label for User channels (`User0` to `User7`).

        Returns:
            str: This channel user label. This is the empty string for non User channels.

        See also:
            :meth:`Channel.type`,
            :class:`ChannelType`.
        """
        return _substance_painter.textureset.channel_user_name(self.channel_id)

    def is_color(self) -> bool:
        """
        Check if the channel is in color or grayscale format.

        Returns:
            bool: ``True`` if the channel format is a color format.
        """
        return _substance_painter.textureset.channel_is_color(self.channel_id)

    def is_floating(self) -> bool:
        """
        Check if the channel is in floating point or normalized fixed point format.

        Returns:
            bool: ``True`` if the channel format is a floating point format.
        """
        return _substance_painter.textureset.channel_is_floating(self.channel_id)

    def bit_depth(self) -> int:
        """
        Get the number of bits per component.

        Returns:
            int: The channel bit depth per component.
        """
        return _substance_painter.textureset.channel_bit_depth(self.channel_id)

    def type(self) -> ChannelType:
        """
        Get the channel type.

        Returns:
            ChannelType: This channel type.

        See also:
            :meth:`Channel.label`.
        """
        return _substance_painter.textureset.channel_type(self.channel_id)

    def edit(self, channel_format: ChannelFormat, label: typing.Optional[str] = None) -> None:
        """
        Change the channel format and label.

        Args:
            channel_format (ChannelFormat): The new texture format of the channel.
            label (str, optional): Label of the channel in case of User channel as type.

        Raises:
            ProjectError: If no project is opened.
            ValueError: If there is no stack labeled ``stack_id`` in this Texture Set.
            ValueError: If there is no channel of type ``channel_type`` in this Texture Set.
            ValueError: If a label was provided but ``channel_type`` is not a user type.
                Standard channel types have fixed labels.
            ValueError: If the channel is invalid.
        """
        if label is None:
            label = ""
        _substance_painter.textureset.edit_channel(self.channel_id, channel_format, label)


@dataclasses.dataclass(frozen=True)
class _FrozenUVTile:
    u: int  #pylint: disable=invalid-name
    v: int  #pylint: disable=invalid-name
    _material_id: int


class UVTile(_FrozenUVTile):
    """
    A UV Tile coordinates.

    :param u: The U coordinate of the UV Tile.
    :param v: The V coordinate of the UV Tile.

    See also:
        :meth:`TextureSet.all_uv_tiles`
    """

    @staticmethod
    def _belong_to_texture_set(uv_tiles: typing.List['UVTile'], material_id: int) -> bool:
        """
        Check that a collection of UV Tiles belong to the given Texture Set.
        Manually initialized UV Tiles with `_material_id` = 0 are ignored.

        Returns:
            bool: Whether all given UV Tiles belong to the given Texture Set.
        """

        def predicate(tiles, material_id):
            for tile in tiles:
                yield tile._material_id in {0, material_id}  #pylint: disable=protected-access

        return any(predicate(uv_tiles, material_id))  #pylint: disable=protected-access

    @property
    def name(self) -> str:
        """
        The name of the UV Tile.

        UV Tile names must be unique within a Texture Set.

        :type: str
        :getter: Get the UV Tile name.
        :setter: Set the UV Tile name.
        :raises ProjectError: If no project is opened.
        :raises ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        :raises ValueError: If the UV Tile is invalid.
        :raises ValueError: If the name of the UV Tile contains reserved characters.
        :raises ValueError: If the name of the UV Tile is not unique within the Texture Set.
        """
        return _substance_painter.textureset.uv_tile_name(self._material_id, (self.u, self.v))

    @name.setter
    def name(self, name: str) -> None:
        _substance_painter.textureset.set_uv_tile_name(self._material_id, (self.u, self.v), name)

    @property
    def description(self) -> str:
        """
        The description of the UV Tile.

        :type: str
        :getter: Get the UV Tile description.
        :setter: Set the UV Tile description.
        :raises ProjectError: If no project is opened.
        :raises ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        :raises ValueError: If the UV Tile is invalid.
        """
        return _substance_painter.textureset.uv_tile_description(self._material_id,
                                                                 (self.u, self.v))

    @description.setter
    def description(self, description: str) -> None:
        _substance_painter.textureset.set_uv_tile_description(self._material_id, (self.u, self.v),
                                                              description)

    def get_resolution(self) -> Resolution:
        """
        Get the UV Tile resolution.

        Returns:
            Resolution: The resolution of this UV Tile in pixels.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance Painter has not started all its services yet.
            ValueError: If the UV Tile is invalid.

        Note:
            The time complexity of this function is linear in the number of UV Tiles in the parent
            Texture Set. If you need to process multiple UV Tiles, please see
            ``TextureSet.get_uvtiles_resolution``.

        See also:
            :meth:`UVTile.set_resolution`
            :meth:`UVTile.reset_resolution`
            :meth:`TextureSet.get_uvtiles_resolution`,
        """
        texture_set_resolution = _substance_painter.textureset.get_resolution(self._material_id)
        uvtiles_resolution = _substance_painter.textureset.get_uvtiles_resolution(self._material_id)
        resolution = uvtiles_resolution.get((self.u, self.v), texture_set_resolution)
        return Resolution(width=resolution[0], height=resolution[1])

    def set_resolution(self, new_resolution: Resolution):
        """
        Set the resolution of the UV Tile.

        See resolution restrictions: :class:`Resolution`.

        Args:
            new_resolution (Resolution): The new resolution for this UV Tile.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance Painter has not started all its services yet.
            ValueError: If ``new_resolution`` is not square.
            ValueError: If ``new_resolution`` is not a valid resolution.
            ValueError: If the UV Tile is invalid.

        Note:
            The time complexity of this function is linear in the number of UVTiles in the parent
            Texture Set. If you need to process multiple UVTiles, please see
            ``TextureSet.set_uvtiles_resolution``.

        See also:
            :meth:`UVTile.get_resolution`,
            :meth:`UVTile.reset_resolution`,
            :meth:`TextureSet.set_resolution`,
            :meth:`TextureSet.set_uvtiles_resolution`,
        """
        resolution = {(self.u, self.v): (new_resolution.width, new_resolution.height)}
        _substance_painter.textureset.set_uvtiles_resolution(texture_set_id=self._material_id,
                                                             resolutions=resolution)

    def reset_resolution(self):
        """
        Reset the resolution of the UV Tile to match the parent Texture Set.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance Painter has not started all its services yet.
            ValueError: If the UV Tile is invalid.

        Note:
            The time complexity of this function is linear in the number of UVTiles in the parent
            Texture Set. If you need to process multiple UVTiles, please see
            ``TextureSet.reset_uvtiles_resolution``.

        See also:
            :meth:`UVTile.get_resolution`,
            :meth:`UVTile.set_resolution`,
            :meth:`TextureSet.reset_uvtiles_resolution`,
        """
        uv_tiles = {(self.u, self.v)}
        _substance_painter.textureset.reset_uvtiles_resolution(texture_set_id=self._material_id,
                                                               uv_tiles=uv_tiles)

    def all_mesh_names(self) -> typing.List[str]:
        """
        Get the list of meshes of the UV Tile.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance Painter has not started all its services yet.
            ValueError: If the UV Tile is invalid.

        See also:
            :meth:`TextureSet.all_mesh_names`
        """
        return sorted(
            _substance_painter.textureset.all_uvtile_mesh_names(self._material_id,
                                                                (self.u, self.v)))


@dataclasses.dataclass(frozen=True)
class Stack:
    """
    A `Substance 3D Painter` paintable stack.

    A stack can contain a number of channels (BaseColor, Specular, Roughness,
    etc.), that correspond to the material. The stack belongs to a Texture Set,
    which may contain one or more stacks.

    Typically, only one stack is used and that stack is transparent to the user.
    Selecting the Texture Set will select its stack. However, a Texture Set can
    use layered materials with custom shaders, in which case a specific stack
    needs to be selected.

    If the Texture Set doesn't use material layering, you can retrieve its stack
    as follows:
    ::

        import substance_painter.textureset

        # Get the unnamed stack of "TextureSetName":
        paintable_stack = substance_painter.textureset.Stack.from_name("TextureSetName")

        # Alternatively, get the stack from a Texture Set instance:
        my_texture_set = substance_painter.textureset.TextureSet.from_name("TextureSetName")
        paintable_stack = my_texture_set.get_stack()

    If the Texture Set `does` use material layering, you can retrieve its stacks
    as follows:
    ::

        import substance_painter.textureset

        # Get the stack called "Mask1" from the Texture Set "TextureSetName":
        paintable_stack = substance_painter.textureset.Stack.from_name("TextureSetName",
                                                                       "Mask1")

        # Alternatively, get the stack from a Texture Set instance:
        my_texture_set = substance_painter.textureset.TextureSet.from_name("TextureSetName")
        paintable_stack = my_texture_set.get_stack("Mask1")

        # Show the name of the stack:
        print(paintable_stack.name())


    It is possible to query, add, remove or edit the channels of a stack:
    ::

        import substance_painter.textureset

        # Get the unnamed stack of "TextureSetName":
        paintable_stack = substance_painter.textureset.Stack.from_name("TextureSetName")

        # List all the channels of the "TextureSetName" Texture Set:
        for k,v in paintable_stack.all_channels().items():
            print("{0}: {1}".format(k, str(v.format())))

        # Add a scattering channel to the "TextureSetName" Texture Set:
        paintable_stack.add_channel(substance_painter.textureset.ChannelType.Scattering,
                                    substance_painter.textureset.ChannelFormat.L8)

        # Query details of the added scattering channel:
        if paintable_stack.has_channel(substance_painter.textureset.ChannelType.Scattering):
            channel = paintable_stack.get_channel(
                substance_painter.textureset.ChannelType.Scattering)
            print("The Texture Set now has a scattering channel with {0} bits per pixel."
                .format(channel.bit_depth()))

        # Change the scattering channel to 16 bits inside the "TextureSetName" Texture Set:
        paintable_stack.edit_channel(
            channel_type = substance_painter.textureset.ChannelType.Scattering,
            channel_format = substance_painter.textureset.ChannelFormat.L16)

        # Remove the scattering channel from "TextureSetName":
        paintable_stack.remove_channel(substance_painter.textureset.ChannelType.Scattering)

    See also:
        :class:`TextureSet`,
        `Texture Set documentation`_.

    .. _Texture Set documentation:
        https://www.adobe.com/go/painter-texture-set
    """
    stack_id: int = None

    @staticmethod
    def from_name(texture_set_name: str, stack_name: str = ""):
        """
        Get a stack from its name.

        Args:
            texture_set_name (str): Texture Set name.
            stack_name (str): Stack name.
                Leave empty if the Texture Set does not use material layering.

        Note:
            The Texture Set and stack names are case sensitive.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If ``texture_set_name`` is not string.
            ValueError: If there is no Texture Set with the name ``texture_set_name``.
            ValueError: If there is no stack with the name ``stack_name``.

        See also:
                :meth:`TextureSet.all_stacks`,
                :meth:`TextureSet.get_stack`.
        """
        return TextureSet.from_name(texture_set_name).get_stack(stack_name)

    def __str__(self):
        stack_name = self.name()
        material_name = self.material().name
        if stack_name:
            return material_name + "/" + stack_name
        return material_name

    def name(self) -> str:
        """
        Get the stack name.
        A stack name is empty if the Texture Set it belongs to uses material layering.

        Returns:
            str: The stack name.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the stack is invalid.
        """
        return _substance_painter.textureset.stack_name(self.stack_id)

    def material(self):
        """
        Get the Texture Set this stack belongs to.

        Returns:
            TextureSet: The Texture Set this stack belongs to.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the stack is invalid.

        See also:
            :class:`TextureSet`,
            :func:`all_texture_sets`.
        """
        return TextureSet(
            material_id=_substance_painter.textureset.material_from_stack(self.stack_id))

    def all_channels(self) -> typing.Dict[ChannelType, Channel]:
        """
        List all the channels of a stack.

        Returns:
            dict[ChannelType, Channel]: Map of all the channels of the stack.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

        See also:
            :meth:`Stack.add_channel`,
            :meth:`Stack.remove_channel`.
        """
        all_channel_types = _substance_painter.textureset.ChannelType.__members__.items()
        return dict(
            map(lambda channel_type: (channel_type[1], self.get_channel(channel_type[1])),
                filter(lambda channel_type: self.has_channel(channel_type[1]), all_channel_types)))

    def add_channel(self,
                    channel_type: ChannelType,
                    channel_format: ChannelFormat,
                    label: typing.Optional[str] = None) -> Channel:
        """
        Add a new channel to a stack.

        Note:
            `add_channel` is not available with material layering.

        Args:
            channel_type (ChannelType): The channel type.
            channel_format (ChannelFormat): The texture format of the new channel.
            label (str, optional): The label of the channel in case of User channel as type.

        Returns:
            Channel: The created channel.

        Raises:
            ProjectError: If no project is opened.
            ValueError: If a channel of type ``channel_type`` already exists in this Texture Set.
            ValueError: If a label was provided but ``channel_type`` is not a user type.
                Standard channel types have fixed labels.
            ValueError: If the stack is invalid.
            ValueError: If the Texture Set uses material layering.

        See also:
            :meth:`Stack.all_channels`,
            :meth:`Stack.remove_channel`,
            :meth:`Stack.edit_channel`.
        """
        if label is None:
            label = ""
        return Channel(
            _substance_painter.textureset.add_channel(self.stack_id, channel_type, channel_format,
                                                      label))

    def remove_channel(self, channel_type: ChannelType) -> None:
        """
        Remove a channel from a stack.

        Note:
            `remove_channel` is not available with material layering.

        Args:
            channel_type (ChannelType): The channel type.

        Raises:
            ProjectError: If no project is opened.
            ValueError: If there is no channel of type ``channel_type`` in this Texture Set.
            ValueError: If the stack is invalid.
            ValueError: If the Texture Set uses material layering.

        See also:
            :meth:`Stack.all_channels`,
            :meth:`Stack.add_channel`,
            :meth:`Stack.edit_channel`.
        """
        _substance_painter.textureset.remove_channel(self.stack_id, channel_type)

    def edit_channel(self,
                     channel_type: ChannelType,
                     channel_format: ChannelFormat,
                     label: typing.Optional[str] = None) -> None:
        """
        Change the texture format and label of a channel.

        Args:
            channel_type (ChannelType): The channel type.
            channel_format (ChannelFormat): The new texture format of the channel.
            label (str, optional): The label of the channel in case of User channel as type.

        Raises:
            ProjectError: If no project is opened.
            ValueError: If there is no stack labeled ``stack_id`` in this Texture Set.
            ValueError: If there is no channel of type ``channel_type`` in this Texture Set.
            ValueError: If a label was provided but ``channel_type`` is not a user type.
                Standard channel types have fixed labels.
            ValueError: If the stack is invalid.

        See also:
            :meth:`Stack.add_channel`,
            :meth:`Stack.remove_channel`.
        """
        self.get_channel(channel_type).edit(channel_format, label)

    def has_channel(self, channel_type: ChannelType) -> bool:
        """
        Check if a channel exists in a stack.

        Args:
            channel_type (ChannelType): The channel type.

        Returns:
            bool: ``True`` if the stack has a channel of the given type, ``False`` otherwise.

        Raises:
            ProjectError: If no project is opened.
            ValueError: If the stack is invalid.

        See also:
            :meth:`Stack.add_channel`,
            :meth:`Stack.remove_channel`.
        """
        return _substance_painter.textureset.has_channel(self.stack_id, channel_type)

    def get_channel(self, channel_type: ChannelType) -> Channel:
        """
        Get an existing channel from its type.

        Args:
            channel_type (Channel): The channel type.

        Returns:
            Channel: The channel.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the channel doesn't exists.

        See also:
            :meth:`Stack.has_channel`,
            :meth:`Stack.add_channel`,
            :meth:`Stack.remove_channel`.
        """
        return Channel(_substance_painter.textureset.get_channel(self.stack_id, channel_type))


@dataclasses.dataclass(frozen=True)
class _FrozenTextureSet:
    material_id: int


class TextureSet(_FrozenTextureSet):
    """
    A `Substance 3D Painter` Texture Set. A Texture Set has a resolution and a
    number of stacks, and can be layered or not.
    It optionally also has a number of UV Tiles.

    It uses a set of baked Mesh map textures. Each Mesh map has a defined MeshMapUsage.

    If the corresponding material is not layered, the Texture Set has just one
    stack, which is transparent to the user. If the material is layered, the
    Texture Set has several stacks.

    Example:
        ::

            import substance_painter.textureset

            # Get the Texture Set "TextureSetName":
            my_texture_set = substance_painter.textureset.TextureSet.from_name("TextureSetName")

            # Show the resolution of the Texture Set:
            resolution = my_texture_set.get_resolution()
            print("The resolution is {0}x{1}".format(resolution.width, resolution.height))

            # Change the resolution of the Texture Set:
            my_texture_set.set_resolution(substance_painter.textureset.Resolution(512, 512))

            # Show information about layering:
            if my_texture_set.is_layered_material():
                print("{0} is a layered material".format(my_texture_set.name()))

                # Get the stack called "Mask1" from the Texture Set:
                mask_stack = my_texture_set.get_stack("Mask1")

                # Print "TextureSetName/Mask1":
                print(mask_stack)

            else:
                print("{0} is not a layered material".format(my_texture_set.name()))

            # Show information about UV Tiles:
            if my_texture_set.has_uv_tiles():
                print("{0} has UV Tiles:".format(my_texture_set.name()))
                for tile in my_texture_set.all_uv_tiles():
                    print("Tile {0} {1}".format(tile.u, tile.v))

            # List all the stacks of the Texture Set "TextureSetName":
            for stack in my_texture_set.all_stacks():
                print(stack)

            # Query ambiant occlusion Mesh map of the Texture Set "TextureSetName":
            usage = substance_painter.textureset.MeshMapUsage.AO
            meshMapResource = my_texture_set.get_mesh_map_resource(usage)

            if meshMapResource is None :
                print("{0} does not have a Mesh map defined for usage {1}"
                    .format(my_texture_set.name(), usage))
            else:
                print("{0} uses {1} Mesh map for usage {2}"
                    .format(my_texture_set.name(), meshMapResource, usage))

            # Unset ambiant occlusion Mesh map of the Texture Set "TextureSetName":
            my_texture_set.set_mesh_map_resource(usage, None)

    See also:
        :class:`Stack`,
        :class:`UVTile`,
        :class:`MeshMapUsage`,
        `Texture Set documentation`_.

    .. _Texture Set documentation:
        https://www.adobe.com/go/painter-texture-set

    :param material_id:
    """

    @staticmethod
    def from_name(texture_set_name: str):
        """
        Get the Texture Set from its name.

        Args:
            texture_set_name (str): The name of the Texture Set.

        Note:
            The Texture Set name is case sensitive.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            TypeError: If ``texture_set_name`` is missing or not a string.
            ValueError: If ``texture_set_name`` is empty.
            ValueError: If there is no Texture Set with the name ``texture_set_name``.
        """
        if not texture_set_name:
            raise ValueError("A string name is required.")
        if not isinstance(texture_set_name, str):
            raise TypeError(_utility.type_mismatch_error_message("texture_set_name", str))

        texture_sets = all_texture_sets()
        try:
            return next(texture_set for texture_set in texture_sets
                        if texture_set.name == texture_set_name)
        except StopIteration as exc:
            raise ValueError(f"Texture Set '{texture_set_name}' not found.") from exc

    def __str__(self):
        return self.name()

    @property
    def original_name(self) -> str:
        """
        The original name of the Texture Set, as it was when it was imported.

        :type: str
        :getter: Get the Texture Set original name.
        :raises ProjectError: If no project is opened.
        :raises ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        :raises ValueError: If the Texture Set is invalid.
        """
        return _substance_painter.textureset.original_material_name(self.material_id)

    @property
    def name(self) -> str:
        """
        The name of the Texture Set.

        Texture Set names must be unique.

        :type: str
        :getter: Get the Texture Set name.
        :setter: Set the Texture Set name.
        :raises ProjectError: If no project is opened.
        :raises ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        :raises ValueError: If the Texture Set is invalid.
        :raises ValueError: If the name of the Texture Set contains reserved characters.
        :raises ValueError: If the name of the Texture Set is not unique.
        """
        ts_name = _substance_painter.textureset.material_name(self.material_id)
        return _utility.make_callable(ts_name)

    @name.setter
    def name(self, name: str) -> None:
        _substance_painter.textureset.set_material_name(self.material_id, name)

    @property
    def description(self) -> str:
        """
        The description of the Texture Set.

        :type: str
        :getter: Get the Texture Set description.
        :setter: Set the Texture Set description.
        :raises ProjectError: If no project is opened.
        :raises ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        :raises ValueError: If the Texture Set is invalid.
        """
        return _substance_painter.textureset.material_description(self.material_id)

    @description.setter
    def description(self, description: str) -> None:
        _substance_painter.textureset.set_material_description(self.material_id, description)

    def is_layered_material(self) -> bool:
        """
        Query if this Texture Set uses material layering.

        Returns:
            bool: ``True`` if the Texture Set uses material layering, ``False`` otherwise.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the Texture Set is invalid.
        """
        return _substance_painter.textureset.is_layered_material(self.material_id)

    def all_stacks(self) -> typing.List[Stack]:
        """
        List all the stacks from this Texture Set.

        Returns:
            list[Stack]: All the stacks of this Texture Set.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the Texture Set is invalid.

        See also:
            :meth:`TextureSet.get_stack`.
        """
        return list(
            map(lambda id: Stack(stack_id=id),
                _substance_painter.textureset.all_stacks(self.material_id)))

    def get_stack(self, stack_name: str = "") -> Stack:
        """
        Get a stack of this Texture Set from its name.

        Args:
            stack_name (str): The stack name.
                Leave empty if the Texture Set does not use material layering.

        Note:
            The stack name is case sensitive.

        Returns:
            Stack: The stack.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the Texture Set is invalid.

        See also:
            :meth:`TextureSet.all_stacks`.
        """
        stacks = self.all_stacks()
        try:
            return next(stack for stack in stacks if stack.name() == stack_name)
        except StopIteration as exc:
            raise ValueError(f"Stack '{stack_name}' not found.") from exc

    def get_resolution(self) -> Resolution:
        """
        Get the Texture Set resolution.

        Returns:
            Resolution: The resolution of this Texture Set in pixels.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If the Texture Set is invalid.

        See also:
            :meth:`TextureSet.set_resolution`,
            :meth:`set_resolutions`.
        """
        resolution = _substance_painter.textureset.get_resolution(self.material_id)
        return Resolution(width=resolution[0], height=resolution[1])

    def set_resolution(self, new_resolution: Resolution):
        """
        Set the resolution of the Texture Set.

        See resolution restrictions: :class:`Resolution`.

        Note:
            For any Texture Set, you can find its accepted resolutions in the
            "Texture Set Settings" window, in the "Size" menu.

        Args:
            new_resolution (Resolution): The new resolution for this Texture Set.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
            ValueError: If ``new_resolution`` is not a valid resolution.
            ValueError: If the Texture Set is invalid.

        See also:
            :meth:`TextureSet.get_resolution`,
            :meth:`set_resolutions`.
        """
        _substance_painter.textureset.set_resolution([self.material_id], new_resolution.width,
                                                     new_resolution.height)

    def has_uv_tiles(self) -> bool:
        """
        Check if the Texture Set uses the UV Tiles workflow.

        Returns:
            bool: ``True`` if the Texture Set uses the UV Tiles workflow, ``False`` otherwise.

        Raises:
            ProjectError: If no project is opened.

        See also:
            :meth:`all_uv_tiles`
        """
        return _substance_painter.textureset.has_uv_tiles(self.material_id)

    def uv_tile(self, u_coord: int, v_coord: int) -> UVTile:
        """
        Get the Texture Set UV Tile at (u, v) coordinates.

        Args:
            u_coord (int): The u coordinate of the UV Tile.
            v_coord (int): The v coordinate of the UV Tile.

        Returns:
            UVTile: The Texture Set UV Tile at (u, v) coordinate.

        Raises:
            ProjectError: If no project is opened.
        """
        return UVTile(u_coord, v_coord, self.material_id)

    def all_uv_tiles(self) -> typing.List[UVTile]:
        """
        Get the list of the Texture Set UV Tiles, ordered by U then V coordinates.

        Returns:
            typing.List[UVTile]: List of the Texture Set UV Tiles, ordered by U then V coordinates.

        Raises:
            ProjectError: If no project is opened.

        See also:
            :meth:`has_uv_tiles`
        """
        return [
            UVTile(*uv_tile, self.material_id)
            for uv_tile in _substance_painter.textureset.all_uv_tiles(self.material_id)
        ]

    def get_uvtiles_resolution(self) -> typing.Dict[UVTile, Resolution]:
        """
        Get all UV Tiles that have a different resolution from the Texture Set, associated
        to their effective resolution.

        Returns:
            typing.Dict[UVTile, Resolution]: The dictionary of uvtiles and their\
                associated resolution.

        Raises:
            ProjectError: If no project is opened.

        See also:
            :meth:`UVTile.get_resolution`
        """
        return _substance_painter.textureset.get_uvtiles_resolution(self.material_id)

    def set_uvtiles_resolution(self, resolutions: typing.Dict[UVTile, Resolution]):
        """
        Set the resolution of the given UV Tiles to the associated resolution.

        Args:
            resolutions (typing.Dict[UVTile, Resolution]): The dictionary of UV Tiles
                and their associated resolution.

        Raises:
            ProjectError: If no project is opened.

        See also:
            :meth:`UVTile.set_resolution`
        """
        res = {(k.u, k.v): (v.width, v.height) for (k, v) in resolutions.items()}
        _substance_painter.textureset.set_uvtiles_resolution(self.material_id, res)

    def reset_uvtiles_resolution(self, uvtiles: typing.List[UVTile]):
        """
        Reset the resolution of the given UV Tiles to the parent Texture Set's resolution.

        Args:
            uvtiles (typing.List[UVTile]): The list of UV Tiles to be reset.

        Raises:
            ProjectError: If no project is opened.

        See also:
            :meth:`UVTile.reset_resolution`
        """
        indices = {(uvtile.u, uvtile.v) for uvtile in uvtiles}
        _substance_painter.textureset.reset_uvtiles_resolution(self.material_id, indices)

    def all_mesh_names(self) -> typing.List[str]:
        """
        Get the list of meshes of the Texture Set.
        When using UV Tiles, the result is the union of the mesh names of every UV Tiles.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance Painter has not started all its services yet.

        See also:
            :meth:`UVTile.all_mesh_names`
        """
        return sorted(_substance_painter.textureset.all_texture_set_mesh_names(self.material_id))

    def get_mesh_map_resource(
            self, usage: MeshMapUsage) -> typing.Optional[substance_painter.resource.ResourceID]:
        """
        Query the Mesh map for the given usage of the Texture Set.

        Args:
            usage(MeshMapUsage): Which Mesh map usage is queried.

        Returns:
            ResourceID: The Mesh map resource or None.
        """
        mesh_map_url = _substance_painter.textureset.get_mesh_map_resource(self.material_id, usage)

        if not mesh_map_url:
            return None

        return substance_painter.resource.ResourceID.from_url(mesh_map_url)

    def set_mesh_map_resource(
            self, usage: MeshMapUsage,
            new_mesh_map: typing.Optional[substance_painter.resource.ResourceID]) -> None:
        """
        Replace the Mesh map for the given usage of the Texture Set.

        Args:
            usage(MeshMapUsage): Which Mesh map usage to replace.
            new_mesh_map(ResourceID, optional): The new Mesh map or None to unset.

        Raises:
            ResourceNotFoundError: If the resource ``new_mesh_map`` is not found or is not of type
                IMAGE.
            ValueError: If the resource is already used for another Mesh map usage for the
                Texture Set.
        """
        _substance_painter.textureset.set_mesh_map_resource(
            self.material_id, usage, '' if not new_mesh_map else new_mesh_map.url())


def set_resolutions(texturesets: typing.List[TextureSet], new_resolution: Resolution):
    """
    Set the same resolution to multiple Texture Sets.

    See resolution restrictions: :class:`Resolution`.

    Note:
        For any Texture Set, you can find its accepted resolutions in the
        "Texture Set Settings" window, in the "Size" menu.

    Args:
        texturesets (list[TextureSet]): The list of Texture Sets to change.
        new_resolution (Resolution): The new resolution for the Texture Sets.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ValueError: If a Texture Set in ``texturesets`` is invalid.
        ValueError: If there are duplicated Texture Sets in ``texturesets``.
        ValueError: If ``new_resolution`` is not a valid resolution.

    See also:
        :class:`Resolution`,
        :meth:`TextureSet.get_resolution`,
        :meth:`TextureSet.set_resolution`.
    """
    textureset_ids = list(map(lambda texture_set: texture_set.material_id, texturesets))
    _substance_painter.textureset.set_resolution(textureset_ids, new_resolution.width,
                                                 new_resolution.height)


def all_texture_sets() -> typing.List[TextureSet]:
    """
    List all the Texture Sets of the current project.

    Returns:
        list[TextureSet]: List of all the Texture Sets of this project.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`TextureSet`.
    """
    return list(
        map(lambda id: TextureSet(material_id=id),
            _substance_painter.textureset.all_texture_sets()))


def get_active_stack() -> Stack:
    """
    Get the currently paintable Texture Set stack.

    Returns:
        Stack: The currently paintable stack.

    Raises:
        ProjectError: If no project is opened.
        RuntimeError: If there is no active stack.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`Stack`,
        :func:`set_active_stack`.
    """
    return Stack(stack_id=_substance_painter.textureset.get_active_stack())


def set_active_stack(stack: Stack) -> None:
    """
    Set the Texture Set stack to be currently paintable.

    Args:
        stack (Stack): The stack to select.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ValueError: If ``stack`` is not a valid Stack.

    See also:
        :class:`Stack`,
        :func:`get_active_stack`.
    """
    _substance_painter.textureset.set_active_stack(stack.stack_id)
