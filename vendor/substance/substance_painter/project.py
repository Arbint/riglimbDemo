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
This module allows to open, create, save and close projects, and change some of
their properties.

First, here is a complete example showing how to use this module:
::

    import substance_painter.project

    # A few declarations used in this example:
    workFolder = "C:/MyWorkDir"
    meshFile = workFolder+"/MeetMat.FBX"
    templateFile = workFolder+"/MyTemplate.spt"
    mySettings = substance_painter.project.Settings(
        import_cameras=True,
        normal_map_format=substance_painter.project.NormalMapFormat.OpenGL)

    # This should print nothing if you just opened Substance 3D Painter,
    # since no project is opened:
    if substance_painter.project.is_open():
        print("There is already a project opened!")


    # Create a project from a file, import cameras from the file, and set up
    # the project for OpenGL:
    substance_painter.project.create(mesh_file_path=meshFile, settings=mySettings)

    # Show the current state of the project:
    if substance_painter.project.is_open():
        print("The project was successfully created.")
    if substance_painter.project.needs_saving():
        print("The project hasn't been saved yet.")
    # At this stage the file path is empty:
    print("The file path of the project is: '{0}'"
        .format(substance_painter.project.file_path()))


    # Save the project to a file:
    substance_painter.project.save_as(workFolder+"/MyNewProject.spp") # No errors
    if not substance_painter.project.needs_saving():
        print("As expected, there is nothing to save since this was just done.")
    print("The file path of the project is now: '{0}'"
        .format(substance_painter.project.file_path()))
    print("The name of the project is now: '{0}'"
        .format(substance_painter.project.name()))

    # ...
    # Do some painting here.
    # ...

    # Create a backup copy of the project, but keep on working on the initial project:
    substance_painter.project.save_as_copy(workFolder+"/MyBackupProject.spp")
    if not substance_painter.project.needs_saving():
        print("Even though a back copy was made, the project still has to be saved.")
    print("The file path of the project is still: '{0}'"
        .format(substance_painter.project.file_path()))

    # ...
    # Do some more painting here.
    # Suppose you make a terrible mistake and want to revert to the backup copy.
    # ...

    # Close the current project; all unsaved changes are lost!
    substance_painter.project.close()
    if not substance_painter.project.is_open():
        print("No project is opened anymore.")

    # Open the backup copy:
    substance_painter.project.open(workFolder+"/MyBackupProject.spp")
    if substance_painter.project.is_open()
        print("Our project is back!")


    # We can save a template from the project:
    substance_painter.project.save_as_template(templateFile, "01_Head")
    substance_painter.project.close()

    # We can now create a new project with that template file:
    substance_painter.project.create(mesh_file_path=meshFile,
                                     template_file_path=templateFile)

    # End of our little example...
    substance_painter.project.close()
"""

import dataclasses
import enum
import json
import warnings
from typing import Any, Callable, List, Optional, Tuple, Union
import uuid
import _substance_painter.project
from . import event
from . import _executor
from . import _utility

ProjectSaveMode = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.project.ProjectSaveMode, __name__, [('Incremental', object())])
"""Save strategy enumeration.

Members:

================= ===========================
Name              Description
================= ===========================
``Full``          Save everything in a new file. Slow but creates the smallest possible file.
``Incremental``   Save only new or modified data. Fast but the file size is not optimal.
================= ===========================
"""

NormalMapFormat = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.project.NormalMapFormat, __name__)
"""The normal map formats that can be used by a `Substance 3D Painter` project.
A project can have either left handed / OpenGL or right handed / DirectX
normal maps.

This corresponds to the menu "Normal Map Format" in the "New project"
dialog.

Members:

================= ===========================
Name              Description
================= ===========================
``OpenGL``        OpenGL tangent space (right handed).
``DirectX``       DirectX tangent space (left handed).
================= ===========================
"""

TangentSpace = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.project.TangentSpace, __name__)
"""The options for computing tangent space in a project. Tangent space can
be evaluated at each vertex, or at each fragment.

This corresponds to the "Compute Tangent Space Per Fragment" checkbox in
the "New project" dialog.

Members:

================= ===========================
Name              Description
================= ===========================
``PerVertex``     Tangent space computed per vertex.
``PerFragment``   Tangent space computed per fragment.
================= ===========================
"""

ProjectWorkflow = _utility.expose_private_obj(  # pylint: disable = invalid-name
    _substance_painter.project.ProjectWorkflow, __name__)
"""The workflow used by a `Substance 3D Painter` project.

By enabling the UV Tiles Workflow for each Texture Set, tiles within the
same Texture Set share a layer stack and can be painted across. By creating
a Texture Set per UV Tile, each tile is placed  in a Texture Set of its own.
This is the legacy workflow and does not allow for painting accross tiles.

This corresponds to the section "UV Tiles (UDIMs)" in the "New project"
dialog.

Members:

======================== ===========================
Name                     Description
======================== ===========================
``Default``              Default workflow (no udim).
``TextureSetPerUVTile``  Udim workflow with one Texture Set per UV Tile (legacy).
``UVTile``               Udim workflow with one Texture Set per material containing
                         multiple UV Tiles.
======================== ===========================
"""


@dataclasses.dataclass
class UsdSettings:
    """
    Specific settings for USD files.

    This corresponds to the options that are available in the File type-specific settings section
    in the "New project" and "Project configuration" dialogs.

    :param scope_name: Scope name of the primitive to load in the hierarchy. The path must be
        absolute. Expected syntax: ``"/my/path/name"``.
        If not specified, default scope name is the root ``"/"``. Only available for USD files.
    :param variants: Define which variant to use for each primitive path. Values are expected in
        JSON format.
        ::

            [
                {
                    "primPath": "/my/path/name",
                    "selectionName: "variantName",
                    "setName": "variantSetName"
                }
            ]

        Only available for USD files.
    :param subdivision_level: The subdivision level is applied only on geometry built with
        subdivision. Only available for USD files.
    :param frame: The frame to import. Only available for animated USD files.
    """
    scope_name: str = "/"
    variants: dict = None
    subdivision_level: int = 1
    frame: int = 0


@dataclasses.dataclass
class GltfSettings:
    """
    Specific settings for GLTF files.

    This corresponds to the options that are available in the File type-specific settings section
    in the "New project" dialog.

    :param invert_normal_maps: Invert normal maps at import. Only available for GLTF files.
    """
    invert_normal_maps: bool = None


@dataclasses.dataclass
class Settings:
    """
    Project configuration options. All options can be set to ``None`` to use the default values.

    This corresponds to the options that are available in the "New project" dialog.

    See also:
        :class:`NormalMapFormat`,
        :class:`TangentSpace`,
        :class:`ProjectWorkflow`,
        :func:`create`,
        `Project configuration documentation`_.

    .. _Project configuration documentation:
        https://www.adobe.com/go/painter-project-configuration

    :param default_save_path: The default save path.
    :param normal_map_format: Normal map system coordinates. OpenGL or DirectX format.
    :param tangent_space_mode: Per vertex or per fragment tangent space.
    :param project_workflow: Project workflow, selected at project creation time.
    :param export_path: Use this path as the default map export path.
    :param default_texture_resolution: Default resolution for all the Texture Sets.
    :param import_cameras: Import cameras from the mesh file.
    :param mesh_unit_scale: Use custom unit scale for input mesh. Painter unit is centimeters.
        If set to 0 or None, use mesh file internal unit scale.
        This setting is necessary for .obj meshes that use units other than centimeters.
    :param mesh_settings: Specific mesh settings.
    :param usd_settings: Deprecated, use mesh_settings instead.
    :type usd_settings: UsdSettings
    """

    # pylint: disable=too-many-instance-attributes
    default_save_path: str = None
    normal_map_format: NormalMapFormat = None
    tangent_space_mode: TangentSpace = None
    project_workflow: ProjectWorkflow = None
    export_path: str = None
    default_texture_resolution: int = None
    import_cameras: bool = None
    mesh_unit_scale: float = None
    mesh_settings: Union[UsdSettings, GltfSettings] = None

    @property
    def usd_settings(self):
        """
        :meta private:
        """
        warnings.warn("usd_settings is deprecated, use mesh_settings instead", DeprecationWarning)
        return self.mesh_settings

    @usd_settings.setter
    def usd_settings(self, value):
        """
        :meta private:
        """
        warnings.warn("usd_settings is deprecated, use mesh_settings instead", DeprecationWarning)
        self.mesh_settings = value


@dataclasses.dataclass
class MeshReloadingSettings:
    """
    Settings used when reloading a mesh.

    This corresponds to the mesh related options that are available in the
    "Project configuration" dialog.

    See also:
        :func:`reload_mesh`,
        `Project configuration documentation`_.

    .. _Project configuration documentation:
        https://www.adobe.com/go/painter-project-configuration

    :param import_cameras: Import cameras from the mesh file.
    :param preserve_strokes: Preserve strokes positions on mesh.
    :param mesh_settings: Specific settings for USD files.
    :param usd_settings: Deprecated, use mesh_settings instead.
    """
    import_cameras: bool = True
    preserve_strokes: bool = True
    mesh_settings: UsdSettings = None

    @property
    def usd_settings(self):
        """
        :meta private:
        """
        warnings.warn("usd_settings is deprecated, use mesh_settings instead", DeprecationWarning)
        return self.mesh_settings

    @usd_settings.setter
    def usd_settings(self, value):
        """
        :meta private:
        """
        warnings.warn("usd_settings is deprecated, use mesh_settings instead", DeprecationWarning)
        self.mesh_settings = value


class _ActionLock:
    """
    Utility class to perform project operations which require locking the project first.
    For some operations, such as :func:`save`, :func:`save_as_copy` and :func:`save_as_template`,
    the project must be locked before the operation can be performed.
    Once the operation is done, the project must be unlocked.
    This class provides a context manager to make lock and unlock regardless of raised errors.

    Example:
        ::

            with substance_painter.project._ActionLock():
                _substance_painter.project.save()

    """

    def __enter__(self):
        _substance_painter.project.do_action(_substance_painter.project.Action.Lock)
        return self

    def __exit__(self, err_type, err_value, traceback):
        _substance_painter.project.do_action(_substance_painter.project.Action.Unlock)


_DEFAULT_SAVE_MODE = ProjectSaveMode.Incremental


def name() -> Optional[str]:
    """
    Return the name of the current project.

    Returns:
        str: The name of the current project, or ``None`` if the project hasn't
        been saved yet.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ProjectError: If no project is opened.
    """
    project_name = _substance_painter.project.name()
    if not project_name:
        return None
    return project_name


def file_path() -> Optional[str]:
    """
    Return the file path of the current project. This is the path where the
    project will be written to when it is saved.

    Returns:
        str: The file path of the current project, or ``None`` if the project
        hasn't been saved yet.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ProjectError: If no project is opened.

    See also:
        :func:`save`,
        :func:`save_as`.
    """
    project_path = _substance_painter.project.file_path()
    if not project_path:
        return None
    return project_path


def close() -> None:
    """
    Close the current project.

    Warning:
        Any unsaved data will be lost.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ProjectError: If no project is opened.
    """
    if _substance_painter.project.state() == _substance_painter.project.State.Closed:
        raise _substance_painter.exception.ProjectError(
            "Cannot close because no project is opened.")
    _substance_painter.project.do_action(_substance_painter.project.Action.Lock)
    _substance_painter.project.do_action(_substance_painter.project.Action.Close)


def open(project_file_path: str) -> None:  # pylint: disable=redefined-builtin
    """
    Open the project located at ``project_file_path``.

    Args:
        project_file_path (str): The path to the project file (with the extension ``.spp``).

    Raises:
        ProjectError: If Substance 3D Painter cannot open the file ``project_file_path``.
        ProjectError: If there is already an opened project.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
    """
    if _substance_painter.project.state() != _substance_painter.project.State.Closed:
        raise _substance_painter.exception.ProjectError(
            "Cannot open project because another one is already opened.")
    _substance_painter.project.open(project_file_path)


def is_open() -> bool:
    """
    Check if a project is already opened.

    Returns:
        bool: ``True`` if a project is opened, ``False`` otherwise.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
    """
    return _substance_painter.project.state() != _substance_painter.project.State.Closed


def needs_saving() -> bool:
    """
    Check if the current project needs to be saved.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ProjectError: If no project is opened.

    Returns:
        bool: ``True`` if the project has modifications and needs to be saved,
        ``False`` otherwise.
    """
    return _substance_painter.project.needs_saving()


def is_in_edition_state() -> bool:
    """
    Check if the current project is ready to work with.

    Raises:
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        ProjectError: If no project is opened.

    Returns:
        bool: ``True`` if the project is ready to work with,
        ``False`` otherwise.

    See also:
        :class:`substance_painter.event.ProjectEditionEntered`,
        :class:`substance_painter.event.ProjectEditionLeft`.
    """
    # Use the internal state in the dispatcher because the public ProjectEditionEntered event
    # is delayed
    return event.DISPATCHER._is_in_edition_state() # pylint: disable=protected-access


def is_busy() -> bool:
    """
    Check if Substance 3D Painter is currently busy.
    If busy, the project cannot be saved at the moment.
    The application may be busy because no project is in edition state,
    or a long process such as baking/export/unwrap process is ongoing.
    The corresponding BusyStatusChanged event is fired when the busy state changes.

    Returns:
        bool: ``True`` if the project is ready to be saved,
        ``False`` otherwise.

    See also:
        :func:`execute_when_not_busy`,
        :class:`substance_painter.event.BusyStatusChanged`.
    """
    return _substance_painter.project.is_busy()


def execute_when_not_busy(callback: Callable[[], None]) -> None:
    """
    Execute the given callback when Substance 3D Painter is not busy.

    Args:
        callback (Callable[[], None]): The callback to be executed.

    See also:
        :func:`is_busy`,
        :class:`substance_painter.event.BusyStatusChanged`.
    """
    return _executor.PROJECT_EXECUTOR.execute_when_not_busy(callback)


def save_as(project_file_path: str, mode: ProjectSaveMode = _DEFAULT_SAVE_MODE) -> None:
    """
    Save the current project by writing it to the file path ``project_file_path``.

    Note:
        If the path ``project_file_path`` doesn't exist yet, new folders will be
        created as needed.
        Save is disabled when Substance 3D Painter is busy and will throw a ProjectError.

    Args:
        project_file_path (string): The file path to save the project to.
        mode (ProjectSaveMode): The save mode (Incremental or Full).

    Raises:
        ProjectError: If Substance 3D Painter cannot save the project.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`ProjectSaveMode`,
        :func:`save`,
        :func:`save_as_copy`.
        :func:`is_busy`.
    """
    if _substance_painter.project.state() == _substance_painter.project.State.Closed:
        raise _substance_painter.exception.ProjectError("Cannot save because no project is opened.")

    if project_file_path is None:
        project_file_path = ""

    with _ActionLock():
        _substance_painter.project.save(project_file_path, mode)


def save(mode: ProjectSaveMode = _DEFAULT_SAVE_MODE) -> None:
    """
    Save the current project by overwriting the previous save.

    Note:
        Save is disabled when Substance 3D Painter is busy and will throw a ProjectError.

    Args:
        mode (ProjectSaveMode): The save mode (Incremental or Full).

    Raises:
        ProjectError: If Substance 3D Painter cannot save the project.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`ProjectSaveMode`,
        :func:`save_as`,
        :func:`save_as_copy`.
        :func:`is_busy`.
    """
    save_as(None, mode)


def save_as_copy(backup_file_path: str, mode: ProjectSaveMode = _DEFAULT_SAVE_MODE) -> None:
    """
    Save a copy of the current project by writing it to the file path
    ``backup_file_path``. This can be used to save backups of the opened project
    without modifying the original file.

    After `save_as_copy` the project is still considered to be located at the
    location it was previously saved to. If the project was not saved, it is
    still considered to not have a saved location.

    Note:
        If the path ``backup_file_path`` doesn't exist yet, new folders will be
        created as needed.
        Save is disabled when Substance 3D Painter is busy and will throw a ProjectError.

    Args:
        backup_file_path (string): The path to write the copy of the project to.
        mode (ProjectSaveMode): The save mode (Incremental or Full).

    Raises:
        ProjectError: If Substance 3D Painter cannot save the copy.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`ProjectSaveMode`,
        :func:`save`,
        :func:`save_as`.
        :func:`is_busy`.
    """
    if _substance_painter.project.state() == _substance_painter.project.State.Closed:
        raise _substance_painter.exception.ProjectError("Cannot save because no project is opened.")

    with _ActionLock():
        _substance_painter.project.save_as_copy(backup_file_path, mode)


def save_as_template(template_file_path: str, texture_set_name: str) -> ProjectSaveMode:
    """
    Save a template based of the current Texture Set or the one specified.

    Note:
        New folders will be created if they are missing.
        Save is disabled when Substance 3D Painter is busy and will throw a ProjectError.

    Warning:
        If the file already exists, it will be overwritten.

    Args:
        template_file_path (string): The save path.
        texture_set_name (string): Name of the Texture Set used as a template.

    Raises:
        ProjectError: If Substance 3D Painter cannot save the template.
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :func:`is_busy`.
    """
    if _substance_painter.project.state() == _substance_painter.project.State.Closed:
        raise _substance_painter.exception.ProjectError("Cannot save because no project is opened.")

    with _ActionLock():
        _substance_painter.project.save_as_template(template_file_path, texture_set_name)


def _settings_to_dict(settings):
    """Convert Settings instance to dict."""
    settings_dict = dataclasses.asdict(settings)
    if isinstance(settings.mesh_settings, UsdSettings):
        settings_dict["mesh_settings_type"] = _substance_painter.project.MeshSettingsType.Usd
        if settings_dict["mesh_settings"]["variants"]:
            variants = settings_dict["mesh_settings"]["variants"]
            settings_dict["mesh_settings"]["variants"] = json.dumps(variants)
    if isinstance(settings.mesh_settings, GltfSettings):
        settings_dict["mesh_settings_type"] = _substance_painter.project.MeshSettingsType.Gltf
    return settings_dict

def create(mesh_file_path: str,
           mesh_map_file_paths: List[str] = None,
           template_file_path: str = None,
           settings: Settings = Settings()):
    """
    Create a new project.
    If an ``OCIO`` environment variable is set, pointing to a .ocio configuration file,
    the project is setup to use the OCIO color management mode defined by that file.
    If the configuration defined by that file is invalid, a ``ProjectError`` is raised and
    no project is created.
    Similary, if a ``PAINTER_ACE_CONFIG`` environment variable is set, pointing to a .json
    preset file, the project is setup to use the ACE color management mode defined by that file.
    If the preset defined in that file is invalid, a ``ProjectError`` is raised and no project
    is created.
    If both environment variables are set, ``OCIO`` will be used.
    If there is not such environment variable, the project uses the Legacy color management mode.

    Note:
        Project settings override the template parameters.

    Args:
        mesh_file_path (string): File path of the mesh to edit.
            Supported file formats: fbx, obj, dae, ply, usd.
        mesh_map_file_paths (list of string): Paths to the additional mesh maps.
        template_file_path (string): Template file path to use to create the project.
        settings (Settings): Configuration options of the new project.

    Raises:
        ProjectError: If Substance 3D Painter cannot create the project.
        ProjectError: If there is already an opened project.
        ProjectError: If an ``OCIO`` environment variable is set to an invalid configuration.
        ProjectError: If an ``PAINTER_ACE_CONFIG`` environment variable is set to an invalid preset.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        TypeError: If ``settings`` is not an instance of Settings.
        ValueError: If the file format of ``mesh_file_path`` is not supported.
        ValueError: If the mesh file ``mesh_file_path`` does not exist.
        ValueError: If any of the mesh map files in ``mesh_map_file_paths`` do not exist.
        ValueError: If the template file ``template_file_path`` doesn't exist.
        ValueError: If the template file ``template_file_path`` is invalid.
        ValueError: If ``settings`` are not valid project settings (see documentation
            of :class:`Settings`).
        ValueError: If ``settings.default_texture_resolution`` is not a valid resolution.

    See also:
        :class:`Settings`,
        `Project creation documentation`_.

    .. _Project creation documentation:
        https://www.adobe.com/go/painter-project-creation
    """
    if is_open():
        raise _substance_painter.exception.ProjectError(
            "Cannot create a new project because one is already opened.")

    if not isinstance(settings, Settings):
        raise TypeError(_utility.type_mismatch_error_message("settings", Settings))

    if mesh_map_file_paths is None:
        mesh_map_file_paths = []
    if template_file_path is None:
        template_file_path = ""

    _substance_painter.project.create(mesh_file_path, mesh_map_file_paths, template_file_path,
                                      _settings_to_dict(settings))


def last_imported_mesh_path() -> str:
    """
    Return the path to the last imported mesh.

    Returns:
        str: The file path of the mesh that was last imported to the project.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
    """
    if not is_open():
        raise _substance_painter.exception.ProjectError(
            "Cannot retrieve mesh path because no project is opened.")
    return _substance_painter.project.last_imported_mesh_path()


def last_saved_substance_painter_version() -> Optional[Tuple[int, int, int]]:
    """
    Return the version of Substance 3D Painter used to last save the project, or None
    if the project is unsaved or was saved with version <= 8.2.0.

    Returns:
        Tuple(int, int, int): The concerned version of Substance 3D Painter, as a major/minor/patch
        tuple.

    Raises:
        ProjectError: If no project is opened.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
    """
    return _substance_painter.project.last_saved_substance_painter_version()


class ReloadMeshStatus(enum.Enum):
    """
    Reload mesh status, used in mesh reload asynchronous callback.

    See also:
        :func:`reload_mesh`,
    """
    SUCCESS = 0
    """Mesh reload was successful."""
    ERROR = 2
    """Mesh reload failed, see application log for details."""


def reload_mesh(mesh_file_path: str, settings: MeshReloadingSettings,
                loading_status_cb: Callable[[ReloadMeshStatus], Any]):
    """
    Import a new mesh to the current project, using the given settings.
    Uses the automatic UV unwrapping settings defined at the project level.

    The loading is asynchronous: this function returns immediately; when
    the loading attempt is finished ``loading_status_cb`` is called with
    an argument indicating if loading was successful.

    Args:
        mesh_file_path (string): File path of the mesh to edit.
            Supported file formats: fbx, obj, dae, ply, usd.
        settings (MeshReloadingSettings): Configuration options for the mesh loading.
        loading_status_cb (Callable[[ReloadMeshStatus], Any]): Loading status notification callback.

    Raises:
        ProjectError: If no project is opened or Substance 3D Painter is busy.
        ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.

    See also:
        :class:`ReloadMeshStatus`,
        :class:`MeshReloadingSettings`,
        :func:`is_busy`,
        `Project creation documentation`_.

    .. _Project creation documentation:
        https://www.adobe.com/go/painter-project-creation
    """

    def event_cb(evt):
        event.DISPATCHER.disconnect(event.ProjectEditionEntered, event_cb)
        loading_status_cb(ReloadMeshStatus.SUCCESS)

    event.DISPATCHER.connect_strong(event.ProjectEditionEntered, event_cb)

    def private_cb(status):
        if status == _substance_painter.project.MeshLoadingStatus.Error:
            event.DISPATCHER.disconnect(event.ProjectEditionEntered, event_cb)
            loading_status_cb(ReloadMeshStatus.ERROR)

    return _substance_painter.project.reload_mesh(mesh_file_path, _settings_to_dict(settings),
                                                  private_cb)


@dataclasses.dataclass(frozen=True)
class BoundingBox:
    """
    Axis-aligned bounding box (AABB).

    :param dimensions: The dimensions (x,y,z) of the bounding box.
    :param center: The center (x,y,z) of the bounding box..
    :param radius: The radius of the bounding box.

    See also:
        :func:`get_scene_bounding_box`,
    """

    dimensions: List[float]
    center: List[float]
    radius: float


def get_scene_bounding_box() -> BoundingBox:
    """
    Return the bounding box of the scene.

    Returns:
        BoundingBox: The bounding box of the scene.

    Raises:
        ProjectError: If no project is opened.
    """
    result = _substance_painter.project.get_scene_bounding_box()
    return BoundingBox(result[0], result[1], result[2])


def get_uuid() -> uuid.UUID:
    """
    Return the UUID of the current project.

    Returns:
        uuid.UUID: The UUID of the current project.

    Raises:
        ProjectError: If no project is opened.
    """
    return uuid.UUID(_substance_painter.project.get_uuid())


class Metadata:
    """
    Project metadata are arbitrary data that can be attached to a `Substance
    Painter` project. When the project is saved, the metadata are saved with it,
    so it is still available the next time the project is loaded.

    Metadata can only be accessed when a project is opened. If no project is
    opened, the methods will raise an exception.

    The constructor of the class ``Metadata`` takes a context name as an
    argument. This context name can be for example the name of your plugin. It
    should be unique, to avoid conflict with other plugins.

    Example:
        ::

            import substance_painter

            # Instantiate the Metadata utility, for the plugin "MyPlugin".
            metadata = substance_painter.project.Metadata("MyPlugin")

            # Store a version number under the key "version".
            plugin_version = { "major": 1, "minor": 0 }
            metadata.set("version", plugin_version)

            # List the project's metadata keys. The key "version" is now present.
            keys = metadata.list()
            print(keys)

            # Retrieve the metadata "version".
            plugin_version = metadata.get("version")
            print("Version: " + str(plugin_version))
    """

    def __init__(self, context: str):
        if not isinstance(context, str):
            raise TypeError(_utility.type_mismatch_error_message("context", str))
        if not context:
            raise ValueError("A Metadata must have a context name.")
        self._context = context

    def list(self) -> list:
        """
        Return the list of project metadata keys.

        Raises:
            ProjectError: If no project is opened.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        """
        return _substance_painter.project.metadata_keys(self._context)

    def get(self, key: str):
        """
        Retrieve the project metadata under the given key.

        The supported data types are:
            - Primitive types: `bool`, `int`, `float`, `str`.
            - `list`
               - Items can be any of the supported data types.
            - `dict`
               - Keys must be of type `str`.
               - Values can be any of the supported data types.

        Args:
            key (str): The key identifying the metadata to retrieve.

        Raises:
            ProjectError: If no project is opened.
            RuntimeError: If the metadata under ``key`` use a type that is not supported.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        """
        return _substance_painter.project.metadata(self._context + "/" + key)

    def set(self, key: str, value):
        """
        Store project metadata under the given key.

        The supported data types are:
            - Primitive types: `bool`, `int`, `float`, `str`.
            - `list`
               - Items can be any of the supported data types.
            - `dict`
               - Keys must be of type `str`.
               - Values can be any of the supported data types.

        Args:
            key (str): The key identifying the metadata to store.
            value: The metadata to store.

        Raises:
            ProjectError: If no project is opened.
            RuntimeError: If ``value`` uses a type that is not supported.
            ServiceNotFoundError: If Substance 3D Painter has not started all its services yet.
        """
        _substance_painter.project.set_metadata(self._context + "/" + key, value)
