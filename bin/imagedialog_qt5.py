# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\usr\Code\Anki\addons\search-to-notes\src\py\imagedialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ImageDialog(object):
    def setupUi(self, ImageDialog):
        ImageDialog.setObjectName("ImageDialog")
        ImageDialog.setWindowModality(QtCore.Qt.NonModal)
        ImageDialog.resize(760, 659)
        ImageDialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.horizontalLayout = QtWidgets.QHBoxLayout(ImageDialog)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gfx = QtWidgets.QLabel(ImageDialog)
        self.gfx.setLineWidth(0)
        self.gfx.setText("")
        self.gfx.setScaledContents(False)
        self.gfx.setIndent(0)
        self.gfx.setObjectName("gfx")
        self.horizontalLayout.addWidget(self.gfx)

        self.retranslateUi(ImageDialog)
        QtCore.QMetaObject.connectSlotsByName(ImageDialog)

    def retranslateUi(self, ImageDialog):
        _translate = QtCore.QCoreApplication.translate
        ImageDialog.setWindowTitle(_translate("ImageDialog", "Dialog"))
