import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mel
from maya.OpenMaya import MVector

from PySide6.QtWidgets import (QMainWindow, 
                               QWidget,
                               QVBoxLayout,
                               QHBoxLayout,
                               QLabel,
                               QPushButton,
                               QSlider,
                               QLineEdit,
                               QMessageBox
                               )
from PySide6.QtCore import Qt
from shiboken6 import wrapInstance

def GetMayaMainWindow()->QMainWindow:
    mayaMainWindow = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindow), QMainWindow)
    return mayaMainWindow


def RemoveWidgetWithName(name):
    for widget in GetMayaMainWindow().findChildren(QWidget, name):
        widget.deleteLater()
        
class LimbRigger:
    def __init__(self):
        self.root = ""
        self.mid = ""
        self.end = ""
        self.controllerSize = 20

    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name) 
        mc.makeIdentity(apply = True) # freeze transformation
        grpName = name + "_grp"
        mc.group(name, n=grpName)
        return name, grpName


    def InitializeJntsFromSelection(self):
        selection = mc.ls(sl=True, type="joint")  
        if len(selection) < 3:
            raise Exception("Wrong selection! Plesae select the root, mid, and end joint of the limb")
        
        root = selection[0]
        mid = selection[1]
        end = selection[2]

        rootChildren = mc.listRelatives(root, type="joint", c=True)
        if mid not in rootChildren:
            raise Exception(f"Wrong selection! {mid} is not a child of {root}")

        midChildren = mc.listRelatives(mid, type="joint", c=True)
        if end not in midChildren:
            raise Exception(f"Wrong selection! {end} is not a child of {mid}")

        self.root = root
        self.mid = mid
        self.end = end

    def MakeFKControllerForJnt(self, jntName):
        ctrlName = "ac_" + jntName
        ctrlGrpName = ctrlName + "_grp"

        mc.circle(n=ctrlName, nr=(1,0,0), r=self.controllerSize)
        mc.group(ctrlName, n = ctrlGrpName)

        mc.matchTransform(ctrlGrpName, jntName)
        mc.orientConstraint(ctrlName, jntName)

        return ctrlName, ctrlGrpName

    def RigLimb(self):
        if self.root == "" or self.mid == "" or self.end == "":
            raise Exception("Please Set the joints first!")
        print(f"Rigging limb with {self.root}, {self.mid}, {self.end}")

        rootCtrl, rootCtrlGrp = self.MakeFKControllerForJnt(self.root)
        midCtrl, midCtrlGrp = self.MakeFKControllerForJnt(self.mid)
        endCtrl, endCtrlGrp = self.MakeFKControllerForJnt(self.end)

        mc.parent(midCtrlGrp, rootCtrl)
        mc.parent(endCtrlGrp, midCtrl)

        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxController("ac_ik_"+self.end)
        mc.matchTransform(ikEndCtrlGrp, self.end)

        rootPos: MVector = self.GetObjectPosition(self.root)
        endPos: MVector = self.GetObjectPosition(self.end)

        # figure out a ik Handle name
        ikHandle = "ikHandle_" + self.end
        # creates the ik handle, sj means the starting joint of the ik, ee is the end joint of the ik
        mc.ikHandle(n = ikHandle, sj = self.root, ee = self.end, sol = "ikRPsolver")

        # mc.getAttr returns the values of the attribute, [0] means we are getting the first one.
        ikPoleVectorCoords = mc.getAttr(f"{ikHandle}.poleVector")[0]
        print(ikPoleVectorCoords)
        ikPoleVector = MVector(ikPoleVectorCoords[0], ikPoleVectorCoords[1], ikPoleVectorCoords[2])
        ikPoleVector.normalize()

        # Arm dir & length
        armVector: MVector = endPos - rootPos

        armLength: float = armVector.length()
        armVector.normalize()

        # Pole Vector position 
        poleVectorPos = rootPos + (ikPoleVector + armVector) * armLength / 2

        poleVectorCtrl = "ac_ik_" + self.mid 
        mc.spaceLocator(n=poleVectorCtrl)

        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(poleVectorCtrl, n=poleVectorCtrlGrp)

        mc.setAttr(f"{poleVectorCtrlGrp}.translate", poleVectorPos[0], poleVectorPos[1], poleVectorPos[2], typ="double3")
        mc.poleVectorConstraint(poleVectorCtrl, ikHandle)

        # sideLabel = "_l_" if rootPos[0] > 0 else "_r_"
        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusShapedController(ikfkBlendCtrl) 

        ikfkBlendPos = rootPos + MVector(rootPos[0], 0, 0)
        mc.setAttr(f"{ikfkBlendCtrlGrp}.translate", ikfkBlendPos[0], ikfkBlendPos[1], ikfkBlendPos[2], typ="double3")

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrl, ln=ikfkBlendAttrName, min = 0, max=1, k=True)

        orientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        ikfkBlendAttrPath = f"{ikfkBlendCtrl}.{ikfkBlendAttrName}"

        mc.expression(s=f"{ikHandle}.ikBlend={ikfkBlendAttrPath}")
        mc.expression(s=f"{ikEndCtrlGrp}.v={ikfkBlendAttrPath}")
        mc.expression(s=f"{poleVectorCtrlGrp}.v={ikfkBlendAttrPath}")
        mc.expression(s=f"{rootCtrlGrp}.v=1-{ikfkBlendAttrPath}")
        mc.expression(s=f"{orientConstraint}.{endCtrl}W0=1-{ikfkBlendAttrPath}")
        mc.expression(s=f"{orientConstraint}.{ikEndCtrl}W1={ikfkBlendAttrPath}")

        mc.parent(ikHandle, ikEndCtrl)
        mc.setAttr(f"{ikHandle}.v", 0)

        topGrpName = self.root + "_rig_grp"
        mc.group(rootCtrlGrp, ikEndCtrlGrp, poleVectorCtrlGrp, ikfkBlendCtrlGrp, n=topGrpName)



    def CreatePlusShapedController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -3 1 0 -p -1 1 0 -p -1 3 0 -p 1 3 0 -p 1 1 0 -p 3 1 0 -p 3 -1 0 -p 1 -1 0 -p 1 -3 0 -p -1 -3 0 -p -1 -1 0 -p -3 -1 0 -p -3 1 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        grpName = name + "_grp"
        mc.group(name, n=grpName)
        return name, grpName


    def GetObjectPosition(self, objectName)->MVector:
        # q means query, t means translate, ws means worldspace, it returns a list of 3 values for x, y, z
        position = mc.xform(objectName, q=True, t=True, ws=True)

        # construct a MVector using the x, y, z position from the position list
        return MVector(position[0], position[1], position[2])



class LimbRiggerWidget(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        RemoveWidgetWithName(self.GetObjectUniqueHash())
        self.setWindowTitle("Limb Rigging Tools") 
        self.setWindowFlags(Qt.WindowType.Window)
        self.setObjectName(self.GetObjectUniqueHash())

        self.limbRigger = LimbRigger()

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        hintLabel = QLabel("Select the root, mid, and end joint of the limb:")
        self.masterLayout.addWidget(hintLabel)

        self.selectionText = QLineEdit(enabled=False)
        self.masterLayout.addWidget(self.selectionText)

        assignSelectionBtn = QPushButton("Set Joints")
        assignSelectionBtn.clicked.connect(self.AssignSelectionBtnClicked)
        self.masterLayout.addWidget(assignSelectionBtn)

        self.ctrlSizeLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.ctrlSizeLayout)

        self.ctrlSizeSlider = QSlider(Qt.Horizontal)
        self.ctrlSizeSlider.setValue(self.limbRigger.controllerSize)
        self.ctrlSizeLayout.addWidget(self.ctrlSizeSlider)

        self.ctrlSizeLabel = QLabel(f"{self.ctrlSizeSlider.value()}")
        self.ctrlSizeLayout.addWidget(self.ctrlSizeLabel)

        self.ctrlSizeSlider.valueChanged.connect(self.CtrlSizeValueChanged)

        rigLimbBtn = QPushButton("Rig Limb") 
        rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)
        self.masterLayout.addWidget(rigLimbBtn)

    def CtrlSizeValueChanged(self, value):
        self.ctrlSizeLabel.setText(f"{value}")
        self.limbRigger.controllerSize = value


    def RigLimbBtnClicked(self):
        try:
            self.limbRigger.RigLimb()
        except Exception as e:
            QMessageBox.critical(None, "Error", f"{e}")

    def AssignSelectionBtnClicked(self):
        try:
            self.limbRigger.InitializeJntsFromSelection()
            self.selectionText.setText(f"{self.limbRigger.root},{self.limbRigger.mid},{self.limbRigger.end}")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"{e}")


    def GetObjectUniqueHash(self):
        return "c40e30335c9475da48d0512244a92c3a"

limbRiggerWidget = LimbRiggerWidget()
limbRiggerWidget.show()