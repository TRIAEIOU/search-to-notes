# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'image_dlg.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_image_dlg(object):
    def setupUi(self, image_dlg):
        image_dlg.setObjectName("image_dlg")
        image_dlg.setWindowModality(QtCore.Qt.NonModal)
        image_dlg.resize(760, 659)
        image_dlg.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.horizontalLayout = QtWidgets.QHBoxLayout(image_dlg)
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.gfx = QtWidgets.QLabel(image_dlg)
        self.gfx.setLineWidth(0)
        self.gfx.setText("")
        self.gfx.setScaledContents(False)
        self.gfx.setIndent(0)
        self.gfx.setObjectName("gfx")
        self.horizontalLayout.addWidget(self.gfx)

        self.retranslateUi(image_dlg)
        QtCore.QMetaObject.connectSlotsByName(image_dlg)

    def retranslateUi(self, image_dlg):
        _translate = QtCore.QCoreApplication.translate
        image_dlg.setWindowTitle(_translate("image_dlg", "Dialog"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    image_dlg = QtWidgets.QDialog()
    ui = Ui_image_dlg()
    ui.setupUi(image_dlg)
    image_dlg.show()
    sys.exit(app.exec_())
