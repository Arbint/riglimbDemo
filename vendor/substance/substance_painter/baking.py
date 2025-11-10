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
The ``baking`` module allows to set baking parameters and launch baking
of mesh maps.

Example:
    ::

        import substance_painter.baking as baking
        import substance_painter.textureset as textureset
        from substance_painter.baking import BakingParameters, MeshMapUsage, CurvatureMethod
        from PySide2 import QtCore

        # set baking parameters
        baking_params = BakingParameters.from_texture_set_name("Name for ts")
        texture_set = baking_params.texture_set()
        common_params = baking_params.common()
        # use QUrl to correctly format the file path with file:/// prefix
        highpoly_mesh_path = QtCore.QUrl.fromLocalFile("C:/Documents/highpoly.fbx").toString()
        ao_params = baking_params.baker(MeshMapUsage.AO)
        BakingParameters.set({
            common_params['OutputSize'] : (10,10),
            common_params['HipolyMesh'] : highpoly_mesh_path,
            ao_params['Distribution'] : ao_params['Distribution'].enum_value('Cosine')})

        # check if common parameters are shared between Texture Sets (True at project creation)
        common_params_are_shared = bool(baking.get_link_group_common_parameters())

        # unlink common parameters. The common parameters for all Texture Sets become independent
        baking.unlink_all_common_parameters()

        # recheck whether common parameters are shared between Texture Sets (now False)
        common_params_are_linked = bool(baking.get_link_group_common_parameters())

        ts1 = textureset.TextureSet.from_name("Name for ts1")
        ts2 = textureset.TextureSet.from_name("Name for ts2")

        # get the list of Texture Sets which are linked for AO with ts1
        # it's not yet linked, so returns only [ts1]
        linked_with_ts1 = baking.get_linked_texture_sets(ts1, MeshMapUsage.AO)

        # link AO baking parameters for ts1 and ts2 together into a group,
        # keeping ts1 parameters for both
        baking.set_linked_group([ts1,ts2], ts1, MeshMapUsage.AO)

        # get the new list of Texture Sets which are linked with ts1
        # now they are linked, so it returns [ts1, ts2]
        linked_with_ts1 = baking.get_linked_texture_sets(ts1, MeshMapUsage.AO)

        # finally unlink AO baking parameters
        baking.unlink_all(MeshMapUsage.AO)

        # get curvature method
        curvature_method = baking_params.get_curvature_method()

        # set curvature method
        baking_params.set_curvature_method(CurvatureMethod.FromMesh)

        # check whether the baking is enabled on the Texture Set level and enable it
        baking_params.is_textureset_enabled()
        baking_params.set_textureset_enabled(True)

        # check if AO usage is enabled for baking and enable it
        baking_params.is_baker_enabled(MeshMapUsage.AO)
        baking_params.set_baker_enabled(MeshMapUsage.AO, True)

        # get all usages enabled for baking
        baking_params.get_enabled_bakers()

        # set usages enabled for baking
        baking_params.set_enabled_bakers([MeshMapUsage.AO, MeshMapUsage.Normal])

        # check if one UV Tile is enabled for baking, disable it
        baking_params.is_uv_tile_enabled(texture_set.uv_tile(0,0))
        baking_params.set_uv_tile_enabled(texture_set.uv_tile(0,0), False)

        # get all UV Tiles enabled for baking
        baking_params.get_enabled_uv_tiles()
        # set UV Tiles enabled for baking
        baking_params.set_enabled_uv_tiles([texture_set.uv_tile(0,0), texture_set.uv_tile(0,1)])

See also:
    :class:`substance_painter.textureset.TextureSet`,
    :class:`substance_painter.textureset.MeshMapUsage`
    :class:`substance_painter.textureset.UVTile`
"""

import dataclasses
import itertools
from typing import List, Dict
import substance_painter.ui
from substance_painter.async_utils import StopSource
from substance_painter.properties import Property, PropertyValue, _to_private_property_value
from substance_painter.textureset import TextureSet, MeshMapUsage, UVTile
import _substance_painter.baking
from . import _utility

BakingStatus = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.baking.BakingStatus, __name__)
"""
Status code of the baking process.

Members:

================= ===========================
Name              Description
================= ===========================
``Success``       The baking was successful.
``Cancel``        The baking was cancelled by the user.
``Fail``          The baking could not complete; the cause is detailed in the log.
================= ===========================
"""

CurvatureMethod = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.baking.CurvatureMethod, __name__)
"""
Members:

``FromMesh``, ``FromNormalMap``
"""


@dataclasses.dataclass(frozen=True)
class BakingParameters:
    """
    Baking parameters for a given texture set.

    Example:
        ::

            # This example shows how to discover the names of the baking parameters
            import substance_painter as sp

            # Get the first texture set of the current project
            textureset = sp.textureset.all_texture_sets()[0]
            # Retrieve baking parameters
            baking_params = sp.baking.BakingParameters.from_texture_set(textureset)

            # Print the keys of the common baking parameters
            print(f'Common: {baking_params.common().keys()}')
            # Print the keys of the baking parameters of the AO mesh map
            print(f'AO: {baking_params.baker(sp.baking.MeshMapUsage.AO).keys()}')

    See also:
        :class:`substance_painter.textureset.TextureSet`,
        :class:`substance_painter.textureset.MeshMapUsage`
    """

    material_id: int

    @staticmethod
    def from_texture_set(texture_set: TextureSet) -> 'BakingParameters':
        """
        Get the baking parameters for the given texture set object.

        Args:
            texture_set (TextureSet): The texture set.

        Returns:
            BakingParameters: The baking parameters for the given texure set.

        See also:
            :class:`substance_painter.textureset.TextureSet`
        """
        return BakingParameters(texture_set.material_id)

    @staticmethod
    def from_texture_set_name(texture_set_name: str) -> 'BakingParameters':
        """
        Get the baking parameters for the given texture set name.

        Args:
            texture_set_name (str): The texture set name.

        Returns:
            BakingParameters: The baking parameters for the given texure set.

        See also:
            :class:`substance_painter.properties.Property`
        """
        return BakingParameters(TextureSet.from_name(texture_set_name).material_id)

    def texture_set(self) -> TextureSet:
        """
        Get the associated texture set.

        Returns:
            TextureSet: The texture set associated with this BakingParameters instance.

        See also:
            :class:`substance_painter.textureset.TextureSet`
        """
        return TextureSet(self.material_id)

    def common(self) -> Dict[str, Property]:
        """
        Get the parameters common to all bakers, like baking resolution.

        Returns:
            Dict[str, Property]: The common parameters.

        See also:
            :class:`substance_painter.properties.Property`
        """
        return {
            Property(x).short_name(): Property(x)
            for x in itertools.chain(_substance_painter.baking.common_parameters(self.material_id),
                                     _substance_painter.baking.detail_parameters(self.material_id))
        }

    def baker(self, baked_map: MeshMapUsage) -> Dict[str, Property]:
        """
        Get the parameters specific to a given baked map.

        Args:
            baked_map (MeshMapUsage): The baked map usage.

        Returns:
            Dict[str, Property]: The corresponding baked map parameters.

        See also:
            :class:`substance_painter.textureset.MeshMapUsage`,
            :class:`substance_painter.properties.Property`
        """
        return {
            Property(x).short_name(): Property(x)
            for x in _substance_painter.baking.baker_parameters(self.material_id, baked_map)
        }

    @staticmethod
    def set(property_values: Dict[Property, PropertyValue]) -> None:
        """
        Set property values in batch.

        Args:
            property_values (Dict[Property, PropertyValue]): A dict of properties
                to be set with their corresponding new values.

        See also:
            :class:`substance_painter.properties.Property`
        """
        _substance_painter.baking.set_tweaks_values([(k.handle, _to_private_property_value(v))
                                                     for k, v in property_values.items()])

    def get_curvature_method(self) -> CurvatureMethod:
        """
        Get the curvature method used for baking

        Returns:
            CurvatureMethod: The curvature method used for baking

        See Also:
            `set_curvature_method`
        """
        return _substance_painter.baking.get_curvature_method(self.material_id)

    def set_curvature_method(self, method: CurvatureMethod):
        """
        Set the curvature method to use for baking

        Args:
            method (CurvatureMethod): The new method to use for baking

        See Also:
            `get_curvature_method`
        """
        _substance_painter.baking.set_curvature_method(self.material_id, method)

    def is_baker_enabled(self, usage: MeshMapUsage) -> bool:
        """
        Whether some usage is enabled for baking.

        Args:
            usage (MeshMapUsage): The baked map usage.

        Returns:
            bool: True if the corresponding usage is enabled for baking.
        """
        return _substance_painter.baking.is_baker_enabled(self.material_id, usage)

    def set_baker_enabled(self, usage: MeshMapUsage, enable: bool) -> None:
        """
        Enable or disable a usage for baking.

        Args:
            usage (MeshMapUsage): The baked map usage.
            enable (bool): Enable or disable.
        """
        _substance_painter.baking.set_baker_enabled(self.material_id, usage, enable)

    def get_enabled_bakers(self) -> List[MeshMapUsage]:
        """
        Get all usages enabled for baking.

        Returns:
            List[MeshMapUsage]: Enabled usages.
        """
        return _substance_painter.baking.get_enabled_bakers(self.material_id)

    def set_enabled_bakers(self, enabled_usages: List[MeshMapUsage]) -> None:
        """
        Set usages enabled for baking. Usages not in this list will be disabled.

        Args:
            enabled_usages (List[MeshMapUsage]): Enabled usages.
        """
        _substance_painter.baking.set_enabled_bakers(self.material_id, enabled_usages)

    def is_textureset_enabled(self) -> bool:
        """
        Whether this Texture Set is enabled for baking.

        Returns:
            bool: True if this Texture Set is enabled for baking.
        """
        return _substance_painter.baking.is_textureset_enabled(self.material_id)

    def set_textureset_enabled(self, enable: bool) -> None:
        """
        Enable or disable this Texture Set for baking.

        Args:
            enable (bool): Enable or disable.
        """
        _substance_painter.baking.set_textureset_enabled(self.material_id, enable)

    def is_uv_tile_enabled(self, uv_tile: UVTile) -> bool:
        """
        Whether a UV Tile is enabled for baking.

        Args:
            tile (UVTile): The UV Tile.

        Returns:
            bool: True if the UV Tile is enabled for baking.

        See also:
            :class:`substance_painter.textureset.TextureSet`,
            :class:`substance_painter.textureset.UVTile`
        """
        if uv_tile._material_id not in {0, self.material_id}:  # pylint: disable = protected-access
            raise ValueError("UV tile must belong to the current texture set.")
        return _substance_painter.baking.is_uv_tile_enabled(self.material_id,
                                                            (uv_tile.u, uv_tile.v))

    def set_uv_tile_enabled(self, uv_tile: UVTile, enable: bool) -> None:
        """
        Enable or disable an UV Tile for baking.

        Args:
            uv_tile (UVTile): The UV Tile.
            enable (bool): Enable or disable.

        See also:
            :class:`substance_painter.textureset.TextureSet`,
            :class:`substance_painter.textureset.UVTile`
        """
        if uv_tile._material_id not in {0, self.material_id}:  # pylint: disable = protected-access
            raise ValueError("UV tile must belong to the current texture set.")
        _substance_painter.baking.set_uv_tile_enabled(self.material_id, (uv_tile.u, uv_tile.v),
                                                      enable)

    def get_enabled_uv_tiles(self) -> List[UVTile]:
        """
        Get all UV Tiles enabled for baking.

        Returns:
            List[UVTile]: Enabled UV Tiles.

        See also:
            :class:`substance_painter.textureset.TextureSet`,
            :class:`substance_painter.textureset.UVTile`
        """
        return [
            UVTile(*coords, self.material_id)
            for coords in _substance_painter.baking.get_enabled_uv_tiles(self.material_id)
        ]

    def set_enabled_uv_tiles(self, enabled_uv_tiles: List[UVTile]) -> None:
        """
        Set UV Tiles enabled for baking. All other tiles will be disabled.

        Args:
            enabled_uv_tiles (List[UVTile]): Enabled UV Tiles.

        See also:
            :class:`substance_painter.textureset.TextureSet`,
            :class:`substance_painter.textureset.UVTile`
        """

        if not UVTile._belong_to_texture_set(  # pylint: disable = protected-access
                enabled_uv_tiles, self.material_id):
            raise ValueError("UV tiles must belong to the current texture set.")

        _substance_painter.baking.set_enabled_uv_tiles(self.material_id,
                                                       [(tile.u, tile.v)
                                                        for tile in enabled_uv_tiles])


def set_linked_group(group: List[TextureSet], reference: TextureSet, usage: MeshMapUsage) -> None:
    """
    Make a group of Texture Sets share the same baking parameters for the given 'usage'. After that,
    editing the 'usage' parameters of one of the group's Texture Set will impact the whole group.

    Args:
        group (List[TextureSet]): Texture Sets to be included in the new group.
        reference (TextureSet): Texture Set which parameters are applied to the whole group.
        usage (MeshMapUsage): Usage of the group.
    """
    _substance_painter.baking.set_linked_group([ts.material_id for ts in group],
                                               reference.material_id, usage)


def set_linked_group_common_parameters(group: List[TextureSet], reference: TextureSet) -> None:
    """
    Make a group of Texture Sets share the same baking common parameters. After that, editing a
    common parameter of one of the group's Texture Set will impact the whole group.

    Args:
        group (List[TextureSet]): Texture Sets to be included in the new group.
        reference (TextureSet): Texture Set which parameters are applied to the whole group.
    """
    _substance_painter.baking.set_linked_group_common_parameters([ts.material_id for ts in group],
                                                                 reference.material_id)


def unlink_all(usage: MeshMapUsage) -> None:
    """
    Unlink all Texture Sets for a given usage. That is, remove the group if it exists, so that all
    Texture Sets have their own copy of the parameters.

    Args:
        usage (MeshMapUsage): Usage to unlink.
    """
    _substance_painter.baking.unlink_all(usage)


def unlink_all_common_parameters() -> None:
    """
    Unlink all Texture Sets for common parameters. That is, remove the group if exists, so that all
    Texture Sets have their own copy of the parameters.
    """
    _substance_painter.baking.unlink_all_common_parameters()


def get_link_group(usage: MeshMapUsage) -> List[TextureSet]:
    """
    Get the list of Texture Sets that share baking parameters for a given usage.

    Args:
        usage (MeshMapUsage): Usage to query.

    Returns:
        List[TextureSet]: All linked Texture Sets for the usage. Empty list if no Texture Set are
        linked.
    """
    return [TextureSet(material_id=id) for id in _substance_painter.baking.get_link_group(usage)]


def get_link_group_common_parameters() -> List[TextureSet]:
    """
    Get the list of Texture Sets that share common baking parameters.

    Returns:
        List[TextureSet]: All linked Texture Sets for common parameters. Empty list if no Texture
        Set are linked.
    """
    return [
        TextureSet(material_id=id)
        for id in _substance_painter.baking.get_link_group_common_parameters()
    ]


def get_linked_texture_sets(texture_set: TextureSet, usage: MeshMapUsage) -> List[TextureSet]:
    """
    Get the list of Texture Sets that share the same parameters as some Texture Set, for a given
    usage.

    Args:
        texture_set (TextureSet): The Texture Set to query
        usage (MeshMapUsage): The usage to query

    Returns:
        List[TextureSet]: The list of Texture Sets sharing parameters with the input Texture Set.
        Contains at least the input Texture Set if no group exists for the usage.
    """
    return [
        TextureSet(material_id=id)
        for id in _substance_painter.baking.get_linked_texture_sets(texture_set.material_id, usage)
    ]


def get_linked_texture_sets_common_parameters(texture_set: TextureSet) -> List[TextureSet]:
    """
    Get the list of Texture Sets that share the same parameters as some Texture Set, for common
    parameters.

    Args:
        texture_set (TextureSet): The Texture Set to query

    Returns:
        List[TextureSet]: The list of Texture Sets sharing common parameters with the input Texture
        Set. Contains at least the input Texture Set if no group exists for common parameters.
    """
    return [
        TextureSet(material_id=id) for id in
        _substance_painter.baking.get_linked_texture_sets_common_parameters(texture_set.material_id)
    ]


def bake_async(texture_set: TextureSet) -> StopSource:
    """
    Launch the baking process for a Texture Set, using the current baking configuration.
    The configuration is set by setting baking parameters, enabling Texture Set, selecting UV Tiles
    for baking, setting curvature method etc.
    This function is asynchronous. When the baking process is finished, the
    :class:`substance_painter.event.BakingProcessEnded` event is sent.

    Args:
        texture_set (TextureSet): The Texture Set to bake.

    Returns:
        StopSource: Can be used to cancel the asynchronous computation.

    See Also:
        :class:`BakingParameters`
        :class:`substance_painter.event.BakingProcessAboutToStart`
        :class:`substance_painter.event.BakingProcessProgress`
        :class:`substance_painter.event.BakingProcessEnded`
        :class:`substance_painter.async_utils.StopSource`
    """
    substance_painter.ui.switch_to_mode(substance_painter.ui.UIMode.Baking)
    return StopSource(_substance_painter.baking.bake_async(texture_set.material_id))


def bake_selected_textures_async() -> StopSource:
    """
    Launch the baking process, using the current baking configuration.
    The configuration is set by setting baking parameters, enabling Texture Set, selecting UV Tiles
    for baking, setting curvature method etc.
    This function is asynchronous. When the baking process is finished, the
    :class:`substance_painter.event.BakingProcessEnded` event is sent.

    Returns:
        StopSource: Can be used to cancel the asynchronous computation.

    See Also:
        :class:`BakingParameters`
        :class:`substance_painter.event.BakingProcessAboutToStart`
        :class:`substance_painter.event.BakingProcessProgress`
        :class:`substance_painter.event.BakingProcessEnded`
        :class:`substance_painter.async_utils.StopSource`
    """
    substance_painter.ui.switch_to_mode(substance_painter.ui.UIMode.Baking)
    return StopSource(_substance_painter.baking.bake_selection_async())
