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
This module exposes functions that change how the model of a project is presented
in the viewports. They correspond to settings available in the "Display
Settings" window.

The Environment Map used to light the scene can be retrieved with
:func:`get_environment_resource()`, or set with :func:`set_environment_resource()`.
The look up table (LUT) used as a Color Profile can be retrieved with
:func:`get_color_lut_resource()`, or set with :func:`set_color_lut_resource()`.

Example:
    ::

        import substance_painter.display

        # Show the currently used color profile:
        color_lut = substance_painter.display.get_color_lut_resource()
        if (color_lut != None):
            print(color_lut.url())
        else:
            print("No color profile is used.")

        # Set a different color profile:
        new_color_lut = substance_painter.resource.ResourceID(context="starter_assets",
                                                              name="sepia")
        substance_painter.display.set_color_lut_resource(new_color_lut)


        # Show the currently used environment map:
        envmap = substance_painter.display.get_environment_resource()
        print(envmap.url())

        # Set a different environment map:
        new_envmap = substance_painter.resource.ResourceID(context="starter_assets",
                                                           name="Bonifacio Street")
        substance_painter.display.set_environment_resource(new_envmap)


        # Show the currently active tone mapping operator:
        try:
            tone_mapping = substance_painter.display.get_tone_mapping()
            print(tone_mapping)
        except RuntimeError:
            print("The project is color managed; tone mapping is not available")

        # Set a different tone mapping:
        try:
            new_tone_mapping = substance_painter.display.ToneMappingFunction.ACES
            substance_painter.display.set_tone_mapping(new_tone_mapping)
        except RuntimeError:
            print("The project is color managed; tone mapping is not available")



See also:
    :mod:`substance_painter.resource`,
    `Color Profile documentation`_,
    `Environment Settings documentation`_,
    `Camera Settings documentation`_.

    .. _Color Profile documentation:
        https://www.adobe.com/go/painter-color-profile

    .. _Environment Settings documentation:
        https://www.adobe.com/go/painter-environment-settings

    .. _Camera Settings documentation:
        https://substance3d.adobe.com/documentation/spdoc/camera-settings-172818743.html
"""
from __future__ import annotations
import dataclasses
import typing
from typing import List

import _substance_painter.display
import substance_painter.resource
from . import _utility

ToneMappingFunction = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.display.ToneMappingFunction, __name__)
"""Tone mapping function used in display.

This corresponds to the "Tone mapping" list in the "Camera settings" section
of the "Display settings" view.

Members:

============ =============================
Name         Description
============ =============================
``Linear``   Transformation from linear to sRGB without any color remapping.
             Color values above 1 are clamped.
``ACES``     Use the standard color remapping from the Academy Color Encoding
             System (ACES).
============ =============================
"""


def get_environment_resource() -> typing.Optional[substance_painter.resource.ResourceID]:
    """
    Get the environment map resource of the active project.

    Returns:
        ResourceID: The environment map resource or None.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    env_map_url = _substance_painter.display.get_environment_resource()
    if not env_map_url:
        return None
    return substance_painter.resource.ResourceID.from_url(env_map_url)


def set_environment_resource(new_env_map: substance_painter.resource.ResourceID) -> None:
    """
    Set the environment map resource of the active project.

    Args:
        new_env_map (ResourceID): The new environment map resource.

    Raises:
        ProjectError: If no project is opened.
        TypeError: If ``new_env_map`` is not a ResourceID.
        ResourceNotFoundError: If the environment map ``new_env_map`` is not found.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    if not isinstance(new_env_map, substance_painter.resource.ResourceID):
        raise TypeError(
            _utility.type_mismatch_error_message("new_env_map",
                                                 substance_painter.resource.ResourceID))
    _substance_painter.display.set_environment_resource(new_env_map.url())


def get_color_lut_resource() -> typing.Optional[substance_painter.resource.ResourceID]:
    """
    Get the color profile LUT resource of the active project.

    Returns:
        ResourceID:  The color profile LUT resource or None.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    lut_url = _substance_painter.display.get_color_lut_resource()
    if not lut_url:
        return None
    return substance_painter.resource.ResourceID.from_url(lut_url)


def set_color_lut_resource(new_color_lut: substance_painter.resource.ResourceID) -> None:
    """
    Set the color profile LUT resource of the active project.

    Args:
        new_color_lut (ResourceID): The new color profile LUT.

    Raises:
        ProjectError: If no project is opened.
        TypeError: If ``new_color_lut`` is not a ResourceID.
        ResourceNotFoundError: If the color profile ``new_color_lut`` is not found.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    if not isinstance(new_color_lut, substance_painter.resource.ResourceID):
        raise TypeError(
            _utility.type_mismatch_error_message("new_color_lut",
                                                 substance_painter.resource.ResourceID))
    _substance_painter.display.set_color_lut_resource(new_color_lut.url())


def get_tone_mapping() -> ToneMappingFunction:
    """
    Get the tone mapping operator used to display the current project.

    Note:
        The tone mapping function is disabled when color management is enabled.
        In that case trying to call get_tone_mapping will throw a RuntimeError.

    Returns:
        ToneMappingFunction: The tone mapping function currently used by
            the project.

    Raises:
        RuntimeError: If the project is color managed.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    return _substance_painter.display.get_tone_mapping()


def set_tone_mapping(new_tone_mapping: ToneMappingFunction) -> None:
    """
    Set the tone mapping operator to display the current project.

    Note:
        The tone mapping function is disabled when color management is enabled.
        In that case trying to call set_tone_mapping will throw a RuntimeError.

    Args:
        new_tone_mapping (ToneMappingFunction): The new tone mapping function
            to use in the project.

    Raises:
        TypeError: If ``new_tone_mapping`` is not a ToneMappingFunction.
        RuntimeError: If the project is color managed.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its
            services yet.
    """
    if not isinstance(new_tone_mapping, ToneMappingFunction):
        raise TypeError(
            _utility.type_mismatch_error_message("new_tone_mapping", ToneMappingFunction))

    _substance_painter.display.set_tone_mapping(new_tone_mapping)


CameraProjectionType = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.display.CameraProjectionType, __name__)
"""Camera projection type.

Members:

================ =============================
Name             Description
================ =============================
``Perspective``  Objects appear smaller when they are far from the camera.
``Orthographic`` Preserves relative size of objects regardless its distance from the camera.
================ =============================
"""


@dataclasses.dataclass
class Camera:
    """
    Allows the manipulation of the properties of an existing Camera.
    Coordinates of the camera are defined in the scene space.

    Example:
        ::

            import substance_painter.display
            import substance_painter.project

            substance_painter.project.open("C:/projects/MeetMat.spp")

            # Get the dimensions of the scene
            bounding_box = substance_painter.project.get_scene_bounding_box()

            # Get the main camera
            camera = substance_painter.display.Camera.get_default_camera()

            # Update camera properties
            camera.projection_type = substance_painter.display.CameraProjectionType.Perspective
            # Move the camera away from the center of the scene
            camera.position = [
                bounding_box.center[0] + 15,
                bounding_box.center[1],
                bounding_box.center[2] + 15]
            # Rotate the camera (45° of Y-axis)
            camera.rotation = [0, 45, 0]
            # Update the camera field of view (in degrees)
            camera.field_of_view = 50

    See also:
        `Camera Settings documentation`_.
        :func:`substance_painter.project.get_scene_bounding_box`

        .. _Camera Settings documentation:
            https://substance3d.adobe.com/documentation/spdoc/camera-settings-172818743.html
    """
    _camera_id: int

    @staticmethod
    def get_default_camera() -> Camera:
        """
        Get the default camera.

        Returns:
            Camera: The default (main) camera.
        Raises:
            ProjectError: If no project is opened.
            RuntimeError: If no camera has been found.
        """
        return Camera(_substance_painter.display.get_default_camera())

    @property
    def position(self) -> List[float]:
        """
        The position (x,y,z) of the camera.

        :getter: Returns the position of the camera.
        :setter: Sets the position of the camera.
        :type: List[float]

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_position(self._camera_id)

    @position.setter
    def position(self, position: List[float]) -> None:
        _substance_painter.display.set_camera_position(self._camera_id, position)

    @property
    def rotation(self) -> List[float]:
        """
        The rotation (x,y,z) of the camera as Euler angles in degrees.

        :getter: Returns the rotation of the camera.
        :setter: Sets the rotation of the camera.
        :type: List[float]

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_rotation(self._camera_id)

    @rotation.setter
    def rotation(self, rotation: List[float]) -> None:
        _substance_painter.display.set_camera_rotation(self._camera_id, rotation)

    @property
    def field_of_view(self) -> float:
        """
        The field of view of the camera in degrees.
        This value is only used if the ``CameraProjectionType`` is ``Perspective``.

        :getter: Returns the field of view of the camera.
        :setter: Sets the field of view of the camera. Value is clamped between 3 and 179.
        :type: float

        Note:
            Modifing the field of view will change the focal length.

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_field_of_view(self._camera_id)

    @field_of_view.setter
    def field_of_view(self, fov: float) -> None:
        _substance_painter.display.set_camera_field_of_view(self._camera_id, fov)

    @property
    def focal_length(self) -> float:
        """
        The focal length of the camera in mm.
        This value is only used if the ``CameraProjectionType`` is ``Perspective``.

        :getter: Returns the focal length of the camera.
        :setter: Sets the focal length of the camera. Value is clamped between 1 and 500.
        :type: float

        Note:
            Modifing the focal length will change the field of view.

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_focal_length(self._camera_id)

    @focal_length.setter
    def focal_length(self, focal_length: float) -> None:
        _substance_painter.display.set_camera_focal_length(self._camera_id, focal_length)

    @property
    def focus_distance(self) -> float:
        """
        The focus distance of the camera.
        Defines the distance at which the focus point is located.

        :getter: Returns the focus distance of the camera.
        :setter: Sets the focus distance of the camera.
            Value is clamped between 0 and 10 * scene radius.
        :type: float

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_focus_distance(self._camera_id)

    @focus_distance.setter
    def focus_distance(self, focus_distance: float) -> None:
        _substance_painter.display.set_camera_focus_distance(self._camera_id, focus_distance)

    @property
    def aperture(self) -> float:
        """
        The aperture of the camera. Defines how wide the Depth of Field will be.

        :getter: Returns the lens radius.
        :setter: Sets the lens radius. Value is clamped between 0 and 1 * scene radius.
        :type: float

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_aperture(self._camera_id)

    @aperture.setter
    def aperture(self, aperture: float) -> None:
        _substance_painter.display.set_camera_aperture(self._camera_id, aperture)

    @property
    def orthographic_height(self) -> float:
        """
        The orthographic height of the camera.
        This value is only used if the ``CameraProjectionType`` is ``Orthographic``.

        :getter: Returns the orthographic height of the camera.
        :setter: Sets the orthographic height of the camera.
        :type: float

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_orthographic_height(self._camera_id)

    @orthographic_height.setter
    def orthographic_height(self, orthographic_height: float) -> None:
        _substance_painter.display.set_camera_orthographic_height(self._camera_id,
                                                                  orthographic_height)

    @property
    def projection_type(self) -> CameraProjectionType:
        """
        The projection type (perspective or orthographic) of the camera.

        :getter: Returns the projection type of the camera.
        :setter: Sets the projection type of the camera.
        :type: CameraProjectionType

        Raises:
            ProjectError: If no project is opened.
        """
        return _substance_painter.display.get_camera_projection_type(self._camera_id)

    @projection_type.setter
    def projection_type(self, projection_type: CameraProjectionType) -> None:
        _substance_painter.display.set_camera_projection_type(self._camera_id, projection_type)
