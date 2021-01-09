import sys, os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox)
from UI import Ui_MainWindow

import hashlib, struct

class MainWindows(QtWidgets.QMainWindow):

    firmware_start_bytes = [b'\x21\xa8', b'\xef\xbe', b'\xad\xde']

    def __init__(self):
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.filePath = ""
        self.isBurnType = False # 默认为非预烧录固件

        self.ui.openFileButton.clicked.connect(lambda:self.selectFile())
        self.ui.CalculateMD5Button.clicked.connect(lambda:self.CalculateFileHash("计算文件 MD5, 请先打开文件", hash_fun=hashlib.md5))
        self.ui.CalculateSHA256Button.clicked.connect(lambda:self.CalculateFileHash( "计算文件 SHA256, 请先打开文件", hash_fun=hashlib.sha256))


    def selectFile(self):
        oldPath = self.filePath
        if oldPath=="":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                    "选择固件",
                                    oldPath,"bin Files (*.bin);;")   # 设置文件扩展名过滤,用双分号间隔
        # print(fileName_choose, filetype)
        self.ui.fileInfoText.setText("")
        self.ui.filePathText.setText(fileName_choose)

        self.filePath = fileName_choose
        # self.isBurn = self.isFileFirmware(fileName_choose)
        if (self.isFileFirmware(self.filePath)):
            self.ui.fileTypeInfo.setText("文件类型：非预烧录固件")
            # print("非预备烧录固件")
        else:
            self.ui.fileTypeInfo.setText("文件类型：预烧录固件（工厂烧录）")
            # print("预烧录固件")
        return (fileName_choose, filetype)

    def isFileFirmware(self, name):
        self.ConversionToBurnFirmware(name)
        isFirmware = False
        if not os.path.exists(name):
            return False
        if name.endswith(".bin"):
            f = open(name, "rb")
            start_bytes = f.read(6)
            f.close()
            for flags in self.firmware_start_bytes:
                if flags in start_bytes:
                    isFirmware = True
                    break
        return isFirmware

    def ConversionToBurnFirmware(self, name):
        bin = b''
        aesFlag = b'\x00'
        size = os.path.getsize(name)

        f = open(name, "rb")
        firmware = f.read()
        f.close()

        bin += aesFlag                # add aes key flag
        bin += struct.pack('I', size) # add firmware length
        bin += firmware               # add firmware content
        sha256Hash = hashlib.sha256(bin).digest()
        bin += sha256Hash             # add parity
        # print("len:" + len(str(sha256Hash.hex().upper())))
        # print("sha256Hash:", sha256Hash.hex().upper())
    def ConversionToNormalFirmware(self):
        pass


    def CalculateFileHash(self, msg, hash_fun):
        if (self.filePath == ""):
            QMessageBox.warning(self, "请选择文件", msg, QMessageBox.Yes)
            self.selectFile()
        if (self.filePath == ""):
            return
        with open(self.filePath, 'rb') as f:
            obj = hash_fun()
            obj.update(f.read())
            _hash = obj.hexdigest()
        self.ui.fileInfoText.setText(str(_hash).upper())
        return str(_hash).upper()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    windows = MainWindows()
    windows.show()
    sys.exit(app.exec_())
