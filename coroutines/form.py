# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'form.ui'
#
# Created: Sat Jan 17 16:37:14 2015
#      by: PyQt4 UI code generator 4.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(400, 300)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.run = QtGui.QPushButton(Form)
        self.run.setObjectName(_fromUtf8("run"))
        self.horizontalLayout.addWidget(self.run)
        self.step = QtGui.QPushButton(Form)
        self.step.setObjectName(_fromUtf8("step"))
        self.horizontalLayout.addWidget(self.step)
        self.pause = QtGui.QPushButton(Form)
        self.pause.setEnabled(False)
        self.pause.setObjectName(_fromUtf8("pause"))
        self.horizontalLayout.addWidget(self.pause)
        self.cancel = QtGui.QPushButton(Form)
        self.cancel.setEnabled(False)
        self.cancel.setObjectName(_fromUtf8("cancel"))
        self.horizontalLayout.addWidget(self.cancel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.log = QtGui.QTextEdit(Form)
        self.log.setObjectName(_fromUtf8("log"))
        self.verticalLayout.addWidget(self.log)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.run.setText(_translate("Form", "Run", None))
        self.step.setText(_translate("Form", "Step", None))
        self.pause.setText(_translate("Form", "Pause", None))
        self.cancel.setText(_translate("Form", "Cancel", None))

