from unreal import (AssetToolsHelpers,
                    AssetImportTask,
                    FbxImportUI,
                    StaticMesh,
                    Texture2D,
                    EditorAssetLibrary,
                    StaticMaterial
                    )
from pathlib import Path
print("hello from vscode!")

class UnrealUtilities:
    def __init__(self):
        self.substanceRootDir = "/Game/Substance/"
        self.substanceTempDir = self.substanceRootDir + "temp" 


    def LoadMeshFromPath(self, meshPath):
        meshName = Path(meshPath).stem
        print(f"mesh name is: {meshName}") 
        importTask = AssetImportTask()

        importTask.replace_existing = True        
        importTask.filename = str(meshPath)
        importTask.destination_path = "/Game/" + meshName
        importTask.automated = True
        importTask.save = True

        fbxImportOptions = FbxImportUI()
        fbxImportOptions.import_mesh = True
        fbxImportOptions.import_as_skeletal = False
        fbxImportOptions.import_materials = False
        fbxImportOptions.static_mesh_import_data.combine_meshes = True

        importTask.options = fbxImportOptions

        AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
        imported = importTask.get_objects()[0]
        print(imported)
        return imported


    def LoadTextureFromPath(self, texturePath):
        importTask = AssetImportTask()
        importTask.replace_existing = True
        importTask.filename = str(texturePath)
        importTask.destination_path = self.substanceTempDir
        importTask.automated = True
        importTask.save = True

        AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])
        imported = importTask.get_objects()[0]
        print(imported)
        return imported

    def ImportFromDir(self, dir):
        meshes = []
        textures = []

        for path in Path(dir).iterdir():
            if ".fbx" in str(path).lower():
                meshes.append(self.LoadMeshFromPath(path))
            else:
                textures.append(self.LoadTextureFromPath(path))

        for mesh in meshes:
            self.BuildMaterialForMesh(mesh, textures)

    
    def BuildMaterialForMesh(self, mesh: StaticMesh, textures: list[Texture2D]):
        meshName = mesh.get_name()
        materialDir = f"/Game/{meshName}/Materials/"
        EditorAssetLibrary.delete_directory(materialDir) # remove the old materials so we can rebuild the new ones
        for i, materialElement in enumerate(mesh.static_materials):
            materialElement: StaticMaterial = materialElement
            print(f"found material: {materialElement.material_slot_name} at index: {i}")
            




UnrealUtilities().ImportFromDir("D:/JT/assets/TestAssets")
