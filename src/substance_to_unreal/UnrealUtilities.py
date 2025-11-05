from unreal import (AssetToolsHelpers,
                    AssetImportTask,
                    FbxImportUI,
                    StaticMesh,
                    Texture2D,
                    EditorAssetLibrary,
                    StaticMaterial,
                    StringLibrary
                    )
from pathlib import Path
print("hello from vscode!")

class UnrealUtilities:
    def __init__(self):
        self.substanceRootDir = "/Game/Substance/"
        self.substanceTempDir = self.substanceRootDir + "temp" 

        self.baseColorName = "BaseColor"
        self.normalName = "Normal"
        self.occRoughnessMetalicName = "OcclusionRoughnessMetallic"


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
            baseColor, normal, occRoughnessMetalic = self.GetTexturesForMaterial(mesh.get_name(), materialElement, textures)
            print(f"texures are:")
            print(baseColor)
            print(normal)
            print(occRoughnessMetalic)

    def GetTexturesForMaterial(self, meshName: str, materialElement: StaticMaterial, textures: list[Texture2D]):
        materialElement: StaticMaterial = materialElement
        materialSlotNameStr = StringLibrary.conv_name_to_string(materialElement.material_slot_name)

        baseColor = None
        normal = None
        occRoughnessMetalic = None

        for texture in textures:
            # is this texture for the mesh
            if meshName not in texture.get_name():
                continue
            
            # is this texture for the material
            if materialSlotNameStr not in texture.get_name():
                continue

            if self.baseColorName in texture.get_name():
                baseColor = texture

            if self.normalName in texture.get_name():
                normal = texture

            if self.occRoughnessMetalicName in texture.get_name(): 
                occRoughnessMetalic = texture

        return baseColor, normal, occRoughnessMetalic 



UnrealUtilities().ImportFromDir("D:/JT/assets/TestAssets")
