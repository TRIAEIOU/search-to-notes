# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\usr\Code\Anki\addons\search-to-notes\src\py\listdialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ListDialog(object):
    def setupUi(self, ListDialog):
        ListDialog.setObjectName("ListDialog")
        ListDialog.resize(400, 500)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ListDialog.sizePolicy().hasHeightForWidth())
        ListDialog.setSizePolicy(sizePolicy)
        ListDialog.setMinimumSize(QtCore.QSize(0, 0))
        ListDialog.setLocale(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
        self.verticalLayout = QtWidgets.QVBoxLayout(ListDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.text = QtWidgets.QTextEdit(ListDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.text.sizePolicy().hasHeightForWidth())
        self.text.setSizePolicy(sizePolicy)
        self.text.setAutoFillBackground(True)
        self.text.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.text.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.text.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.text.setReadOnly(True)
        self.text.setObjectName("text")
        self.verticalLayout.addWidget(self.text)
        self.buttonBox = QtWidgets.QDialogButtonBox(ListDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ListDialog)
        self.buttonBox.accepted.connect(ListDialog.accept) # type: ignore
        self.buttonBox.rejected.connect(ListDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(ListDialog)

    def retranslateUi(self, ListDialog):
        _translate = QtCore.QCoreApplication.translate
        ListDialog.setWindowTitle(_translate("ListDialog", "Dialog"))
