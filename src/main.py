#!/bin/python3
# -*- coding: utf-8 -*-
import binascii
import sys
import time
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QFileDialog, QMessageBox)
from _ui import Ui_MainWindow
from enum import Enum, unique

import hashlib
import struct
import threading


@unique
class FileType(Enum):
    TYPE_FIRMWARE = 1
    TYPE_BURN_FIRMWARE = 2
    TYPE_UNKNOWN = 3


class MainWindows(QtWidgets.QMainWindow):

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

        self.ui.ConversionToNormalButton.clicked.connect(
            lambda: self.ConversionToNormalFirmware(self.savePath))

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
        # print(self.filePath)
        file_type = self.getfileType(self.filePath)
        if (file_type == FileType.TYPE_FIRMWARE):
            self.ui.fileTypeInfo.setText("文件类型：K210 SDK 固件")
        elif (file_type == FileType.TYPE_BURN_FIRMWARE):
            self.ui.fileTypeInfo.setText("文件类型：K210 预烧录固件（ FLASH 工厂烧录）")
        else:
            self.ui.fileTypeInfo.setText("文件类型：未知类型文件")
        return (fileName_choose, filetype)

    def isFirmware(self, file):
        f = open(file, "rb")
        start_bytes = f.read(6)
        for flags in self.firmware_start_bytes:
            if flags not in start_bytes:
                return False
        return True

    def isBurnFirmware(self, file):
        '''
        | 固件描述 | 起始地址 | 占用大小（字节）| 备注 |
        | --- | --- | --- | --- |
        | 头部校验信息 | 0x00 | 5Byte | aseflag(0x00)+固件大小(4byte)  |
        | 固件内容(原始固件) | 0x00 | 6Byte | MagicFlag |
        | 尾部信息 | --- | 32Byte | SHA256(头部校验信息+原始固件) |
        '''
        headFlagSize = 5
        sha256FlagSize = 32
        aseFlag = b'\x00'
        file_size = os.path.getsize(file)
        firmware_size = file_size - headFlagSize - sha256FlagSize
        # print("file_size:" + str(file_size))
        # print("firmware_size:" + str(firmware_size))
        if (firmware_size <= (0)):
            return False
        else:
            # import binascii
            f = open(file, 'rb')
            headflag = f.read(5)
            firmwareSizeflag = struct.unpack("I", headflag[1:5])[0]
            f.seek(0)
            bin = f.read(firmwareSizeflag + headFlagSize)
            sha256Hash = hashlib.sha256(bin).digest()
            # print("固件大小："+str(firmwareSizeflag))
            # print("sha256Hash:" + str(binascii.b2a_hex(sha256Hash))) #读出来是正确的

            # 读取末尾 SHA256
            sha256HashOffset = file_size-sha256FlagSize
            f.seek(sha256HashOffset)
            sha256flag = f.read(sha256FlagSize)
            # print("偏移地址："+ str(sha256HashOffset))
            # print("sha256flag:" + str(binascii.b2a_hex(sha256flag))) #读出来是正确的
            f.close()

            if (headflag[0] != int(aseFlag[0])):
                return False
            if (firmwareSizeflag != firmware_size):
                print("firmware[%s:%s]" % (firmwareSizeflag, firmware_size))
                return False
            if (sha256flag != sha256Hash):
                print("sha256[%s]:[%s]" % (sha256flag, sha256Hash))
                return False
            return True

    def getfileType(self, name):
        file_type = FileType.TYPE_UNKNOWN  # 未知类型
        if not os.path.exists(name):
            QMessageBox.warning(self, "选择固件", "路径错误，请重新选择", QMessageBox.Yes)
            return False
        if name.endswith(".bin"):
            if (self.isFirmware(name)):
                file_type = FileType.TYPE_FIRMWARE
            elif(self.isBurnFirmware(name)):
                file_type = FileType.TYPE_BURN_FIRMWARE
            else:
                file_type = FileType.TYPE_UNKNOWN
        return file_type

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
        # print("sha256Hash:" + str(binascii.b2a_hex(sha256Hash)))
        bin += sha256Hash             # add parity

        with open(self.savePath, "wb") as f:
            f.write(bin)
        self.packing = False

    def ConversionToBurnFirmware(self, name):
        if not os.path.exists(self.savePath):
            self.savePath = os.getcwd()
        if (self.isBurnFirmware(self.filePath)):
            QMessageBox.warning(self, "转换 FLASH 预烧录固件",
                                "固件为 FLASH 预烧录固件，无需转换", QMessageBox.Yes)
            return False
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
            time.sleep(0.5)
            pass
        QMessageBox.information(self, "转换 FLASH 预烧录固件成功！",
                                "固件保存路径：" + self.savePath)

    def exportBinProccess(self, fileName, saveFileName):
        self.packing = True
        headFlagSize = 5
        sha256FlagSize = 32
        file_size = os.path.getsize(fileName)
        firmware_size = file_size - headFlagSize - sha256FlagSize
        if (firmware_size <= (0)):
            self.packing = False
            return False
        else:
            f = open(fileName, 'rb')
            headflag = f.read(5)
            firmwareSizeflag = struct.unpack("I", headflag[1:5])[0]
            f.seek(headFlagSize)
            firmware = f.read(firmwareSizeflag)
            with open(saveFileName, "wb") as f:
                f.write(firmware)
        self.packing = False

    def ConversionToNormalFirmware(self, name):
        if not os.path.exists(self.filePath):
            self.selectFile()
        if not os.path.exists(self.savePath):
            self.savePath = os.getcwd()
        if (self.isFirmware(self.filePath)):
            QMessageBox.warning(self, "转换为 K210 原始固件",
                                "固件为原始固件，无需转换", QMessageBox.Yes)
            return False
        elif (not self.isBurnFirmware(self.filePath)):
            QMessageBox.warning(self, "转换为 K210 原始固件",
                                "非 K210 固件，请重新选择", QMessageBox.Yes)
            return False
        fileName_choose, filetype = QFileDialog.getSaveFileName(self,
                                                                "Save File",
                                                                self.savePath,
                                                                "Binary file (*.bin)")
        if not fileName_choose.endswith(".bin"):
            fileName_choose += ".bin"
        self.savePath = fileName_choose
        self.packing = True

        t = threading.Thread(target=self.exportBinProccess,
                             args=(self.filePath, self.savePath))
        t.setDaemon(True)
        t.start()
        while (self.packing):
            time.sleep(0.5)
            pass
        QMessageBox.information(self, "转换为 K210 原始固件成功！",
                                "固件保存路径：" + self.savePath)

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
