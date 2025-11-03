from unreal import AssetToolsHelpers
from pathlib import Path
print("hello from vscode!")

class UnrealUtilities:
    def __init__(self):
        pass


    def LoadMeshFromPath(self, meshPath):
        meshName = Path(meshPath).stem
        print(f"mesh name is: {meshName}") 


UnrealUtilities().LoadMeshFromPath("D:/JT/assets/TestAssets/Tiffa.fbx")
