import maya.cmds as mc
import maya.OpenMayaUI as omui
import maya.mel as mel
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