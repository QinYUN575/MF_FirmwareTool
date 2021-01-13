import sys
import time
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox)
from _ui import Ui_MainWindow

import hashlib
import struct
import threading


class MainWindows(QtWidgets.QMainWindow):
    TYPE_BURN_FIRMWARE = 1
    TYPE_K210_FIRMWARE = 2
    TYPE_UNKNOWN = 3

    firmware_start_bytes = [b'\x21\xa8', b'\xef\xbe', b'\xad\xde']

    def __init__(self):
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.filePath = ""
        self.savePath = ""
        self.packing = False
        self.isBurnType = False  # 默认为非预烧录固件

        self.ui.openFileButton.clicked.connect(lambda: self.selectFile())
        self.ui.CalculateMD5Button.clicked.connect(
            lambda: self.CalculateFileHash("计算文件 MD5, 请先打开文件", hash_fun=hashlib.md5))
        self.ui.CalculateSHA256Button.clicked.connect(
            lambda: self.CalculateFileHash("计算文件 SHA256, 请先打开文件", hash_fun=hashlib.sha256))

        self.ui.ConversionToBurnButton.clicked.connect(
            lambda: self.ConversionToBurnFirmware(self.filePath))

    def selectFile(self):
        oldPath = self.filePath
        if oldPath == "":
            oldPath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getOpenFileName(self,
                                                                "选择固件",
                                                                oldPath, "bin Files (*.bin);;")   # 设置文件扩展名过滤,用双分号间隔
        # print(fileName_choose, filetype)
        self.ui.fileInfoText.setText("")
        self.ui.filePathText.setText(fileName_choose)
        self.filePath = fileName_choose
        if (self.isFileFirmware(self.filePath)):
            self.ui.fileTypeInfo.setText("文件类型：非预烧录固件")
        else:
            self.ui.fileTypeInfo.setText("文件类型：预烧录固件（工厂烧录）")
        return (fileName_choose, filetype)

    def isFileFirmware(self, name):
        file_type = self.TYPE_BURN_FIRMWARE
        isFirmware = False
        if not os.path.exists(name):
            # QMessageBox.warning(self, "选择固件", "路径错误，请重新选择", QMessageBox.Yes)
            return False
        if name.endswith(".bin"):
            f = open(name, "rb")
            start_bytes = f.read(6)
            for flags in self.firmware_start_bytes:
                if flags in start_bytes:
                    isFirmware = True
                    file_type = self.TYPE_K210_FIRMWARE
                    break
        return isFirmware, file_type

    def mergeBinProccess(self, fileName, saveFileName):
        self.packing = True
        bin = b''
        aesFlag = b'\x00'

        size = os.path.getsize(self.filePath)
        f = open(self.filePath, "rb")
        firmware = f.read()
        f.close()

        bin += aesFlag                # add aes key flag
        bin += struct.pack('I', size)  # add firmware length
        bin += firmware               # add firmware content
        sha256Hash = hashlib.sha256(bin).digest()
        bin += sha256Hash             # add parity

        with open(self.savePath, "wb") as f:
            f.write(bin)
        self.packing = False

    def ConversionToBurnFirmware(self, name):
        if not os.path.exists(self.savePath):
            self.savePath = os.getcwd()
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                "Save File",
                                                                self.savePath,
                                                                "Binary file (*.bin)")
        if not fileName_choose.endswith(".bin"):
            fileName_choose += ".bin"
        self.savePath = fileName_choose
        self.packing = True

        t = threading.Thread(target=self.mergeBinProccess,
                             args=(fileName_choose, self.savePath))
        t.setDaemon(True)
        t.start()
        while (self.packing):
            time.sleep(1)
            pass
        QMessageBox.information(self, "打包固件", "固件保存路径：" + self.savePath)

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
