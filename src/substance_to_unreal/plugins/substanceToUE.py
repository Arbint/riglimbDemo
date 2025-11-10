from pathlib import Path
import os
import substance_painter
from PySide6.QtGui import QAction
import shutil
import remote_execution
import threading


def SendToUnrealEngine():
    # filePath will be where the substane project is
    filePath = Path(substance_painter.project.file_path())

    # exportDir is a folder under the same folder ofthe filePath
    exportDir = str(filePath.parent / substance_painter.project.name())

    # if the exportDir already exists, remove the entire dir so we can export new ones
    if os.path.exists(exportDir):
        shutil.rmtree(exportDir)

    # make the exportDir
    os.makedirs(exportDir, exist_ok=True)
    print(f"exporting to: {exportDir}")

    textureSets = substance_painter.textureset.all_texture_sets()
    exportList = []
    for textureSet in textureSets:
        exportList.append({"rootPath":str(textureSet)})

    print(exportList)
    exportPreset = substance_painter.resource.ResourceID(
        context="starter_assets",
        name = "Unreal Engine (Packed)"
    )

    exportConfig = {
        "exportShaderParams" : False,
        "exportPath" : exportDir,
        "defaultExportPreset": exportPreset.url(),
        "exportList": exportList,
        "exportParameters":
        [
            {
                "parameters":
                {
                    "fileFormat": "tga",
                    "bitDepth": "8",
                    "dithering": True,
                    "paddingAlgorithm":"infinite"
                }
            }
        ]
    }

    substance_painter.export.export_project_textures(exportConfig)
    meshName = substance_painter.project.name() + ".fbx"
    meshExportPath = str(Path(exportDir) / meshName)
    substance_painter.export.export_mesh(meshExportPath, substance_painter.export.MeshExportOption.BaseMesh)

    pluginDir = Path(__file__).parent.parent
    libPath = str(pluginDir / "modules" / "UnrealUtilities.py")

    with open(libPath, "r") as libFile:
        lines = libFile.readlines()
    
    exportDir = exportDir.replace("\\", "/")
    lines.append(f"\nUnrealUtilities().ImportFromDir('{exportDir}')")
    command = "".join(lines)
    print(command)
    
    thread = threading.Thread(target=SendComandToUnrealEngine, args=(command,))
    thread.start()


def SendComandToUnrealEngine(command):
    try:
        remoteExc = remote_execution.RemoteExecution()
        remoteExc.start()
        remoteExc.open_command_connection(remoteExc.remote_nodes)
        remoteExc.run_command(command)
        remoteExc.stop()

    except Exception as e:
        print("Error when sending command to unreal: {e}")


def start_plugin():
    print("start substance to ue")
    sendToUnrealAction = QAction("Send to Unreal Engine", triggered = SendToUnrealEngine)
    substance_painter.ui.add_action(substance_painter.ui.ApplicationMenu.File, sendToUnrealAction)
    substance_painter.ui.sendToUnrealAction = sendToUnrealAction

def close_plugin():
    print("closing substance to ue")