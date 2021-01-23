# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'firmwareChecker3.ui'
#
# Created by: PyQt5 UI code generator 5.15.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        font = QtGui.QFont()
        # font.setFamily("微软雅黑")
        font.setPointSize(14)
        MainWindow.resize(620, 278)
        self.centralwidget = QtWidgets.QWidget(MainWindow)

        self.ConversionToBurnButton = QtWidgets.QPushButton(self.centralwidget)
        self.ConversionToBurnButton.setGeometry(QtCore.QRect(330+50, 80, 221, 51))

        self.ConversionToNormalButton = QtWidgets.QPushButton(self.centralwidget)
        self.ConversionToNormalButton.setGeometry(QtCore.QRect(330+50, 140, 221, 51))

        self.fileTypeInfo = QtWidgets.QLabel(self.centralwidget)
        self.fileTypeInfo.setGeometry(QtCore.QRect(10, 60, 350, 51))
        font.setPointSize(12)
        self.fileTypeInfo.setFont(font)

        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(10, 160, 350, 81))
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 350, 79))

        self.fileInfoText = QtWidgets.QTextEdit(self.scrollAreaWidgetContents)
        self.fileInfoText.setGeometry(QtCore.QRect(0, 0, 350, 81))
        font.setPointSize(14)
        self.fileInfoText.setFont(font)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.CalculateMD5Button = QtWidgets.QPushButton(self.centralwidget)
        self.CalculateMD5Button.setGeometry(QtCore.QRect(330+50, 200, 101, 51))

        self.CalculateSHA256Button = QtWidgets.QPushButton(self.centralwidget)
        self.CalculateSHA256Button.setGeometry(QtCore.QRect(330+110+50, 200, 111, 51))

        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(10, 120, 251, 51))
        font.setPointSize(12)
        self.label_2.setFont(font)

        self.filePathText = QtWidgets.QLineEdit(self.centralwidget)
        self.filePathText.setGeometry(QtCore.QRect(10, 30, 350, 31))

        self.openFileButton = QtWidgets.QPushButton(self.centralwidget)
        self.openFileButton.setGeometry(QtCore.QRect(330+50, 20, 221, 51))

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)

        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "K210 固件转换工具"))
        MainWindow.setWindowIcon(QIcon('./icon_firmware.png'))
        self.ConversionToBurnButton.setText(_translate("MainWindow", "转换为 K210 FLASH 预烧录固件"))
        self.ConversionToNormalButton.setText(_translate("MainWindow", "转换为 K210 原始固件"))
        self.fileTypeInfo.setText(_translate("MainWindow", "文件类型："))
        self.fileInfoText.setText("")
        self.CalculateMD5Button.setText(_translate("MainWindow", "计算文件 MD5"))
        self.CalculateSHA256Button.setText(_translate("MainWindow", "计算文件 SHA256"))
        self.label_2.setText(_translate("MainWindow", "文件信息(MD5/SHA256)"))
        self.openFileButton.setText(_translate("MainWindow", "打开固件 (BIN 文件)"))


class MainWindows(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    windows = MainWindows()
    windows.show()
    sys.exit(app.exec_())
