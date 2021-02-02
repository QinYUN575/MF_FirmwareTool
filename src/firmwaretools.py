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


@unique
class FileType(Enum):
    TYPE_FIRMWARE = 1
    TYPE_BURN_FIRMWARE = 2
    TYPE_UNKNOWN = 3


class MainWindows(QtWidgets.QMainWindow):

    firmware_start_bytes = [b'\x21\xa8', b'\xef\xbe', b'\xad\xde']
    firmware_start_bytes_lenght = 6

    def __init__(self):
        super(MainWindows, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.filePath = ""
        self.saveFilePath = ""
        self.packing = False
        self.fileType = FileType.TYPE_UNKNOWN
        self.isBurnType = False  # 默认为非预烧录固件

        self.ui.openFileButton.clicked.connect(
            lambda: self.selectOpenFile(self.filePath))
        self.ui.CalculateMD5Button.clicked.connect(
            lambda: self.CalculateFileHash("计算文件 MD5, 请先打开文件", hash_fun=hashlib.md5))
        self.ui.CalculateSHA256Button.clicked.connect(
            lambda: self.CalculateFileHash("计算文件 SHA256, 请先打开文件", hash_fun=hashlib.sha256))

        self.ui.ConversionToBurnButton.clicked.connect(
            lambda: self.ConversionToBurnFirmware(self.filePath))

        self.ui.ConversionToNormalButton.clicked.connect(
            lambda: self.ConversionToNormalFirmware(self.filePath))

    def isFirmware(self, file):
        fp = open(file, "rb")
        start_bytes = fp.read(self.firmware_start_bytes_lenght)
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
            fp = open(file, 'rb')
            headflag = fp.read(headFlagSize)
            firmwareSizeflag = struct.unpack("I", headflag[1:5])[0]
            fp.seek(0)
            bin = fp.read(firmwareSizeflag + headFlagSize)
            sha256Hash = hashlib.sha256(bin).digest()
            # print("固件大小："+str(firmwareSizeflag))
            # print("sha256Hash:" + str(binascii.b2a_hex(sha256Hash))) #读出来是正确的

            # 读取末尾 SHA256
            sha256HashOffset = file_size-sha256FlagSize
            fp.seek(sha256HashOffset)
            sha256flag = fp.read(sha256FlagSize)
            # print("偏移地址："+ str(sha256HashOffset))
            # print("sha256flag:" + str(binascii.b2a_hex(sha256flag))) #读出来是正确的
            fp.close()

            if (headflag[0] != int(aseFlag[0])):
                return False
            if (firmwareSizeflag != firmware_size):
                print("firmware[%s:%s]" % (firmwareSizeflag, firmware_size))
                return False
            if (sha256flag != sha256Hash):
                print("sha256[%s]:[%s]" % (sha256flag, sha256Hash))
                return False
            # 验证是否为有 K210 固件标志
            start_bytes = bin[headFlagSize:headFlagSize +
                              self.firmware_start_bytes_lenght]
            for flags in self.firmware_start_bytes:
                if flags not in start_bytes:
                    return False
            return True

    def getfileType(self, filePath):
        file_type = FileType.TYPE_UNKNOWN  # 未知类型
        if filePath.endswith(".bin"):
            if (self.isFirmware(filePath)):
                file_type = FileType.TYPE_FIRMWARE  # K210 原始固件
            elif(self.isBurnFirmware(filePath)):
                file_type = FileType.TYPE_BURN_FIRMWARE  # K210 FLASH 预烧录固件
        return file_type

    def selectOpenFile(self, filePath, handler=None):
        oldFilePath = filePath  # 用户记录上次打开文件的路径
        if oldFilePath == "":
            oldFilePath = os.getcwd()
        filePathChoose, fileTypeFilter = QFileDialog.getOpenFileName(self,
                                                                     "选择固件", oldFilePath, "bin Files(*.bin);;")
        # print(filePathChoose, fileTypeFilter)
        if not os.path.exists(filePathChoose):
            return
        self.filePath = filePathChoose
        self.fileType = self.getfileType(self.filePath)
        # print("filePath:" + self.filePath)

        # self.ui.fileInfoText.setText("")
        self.ui.filePathText.setText(self.filePath)

        if self.fileType == FileType.TYPE_FIRMWARE:
            self.ui.fileTypeInfo.setText("文件类型：K210 SDK 固件")
        elif (self.fileType == FileType.TYPE_BURN_FIRMWARE):
            self.ui.fileTypeInfo.setText("文件类型：K210 预烧录固件（ FLASH 工厂烧录）")
        else:
            self.ui.fileTypeInfo.setText("文件类型：未知类型文件")

        # 回调处理
        if handler != None:
            handler(self.filePath)

    def CalculateFileHash(self, msg, hash_fun):
        if (self.filePath == ""):
            QMessageBox.warning(self, "计算文件签名", msg, QMessageBox.Yes)
            self.selectOpenFile(self.filePath)
        if (self.filePath == ""):
            return
        with open(self.filePath, 'rb') as f:
            obj = hash_fun()
            obj.update(f.read())
            _hash = obj.hexdigest()
        self.ui.fileInfoText.setText(str(_hash).upper())
        return str(_hash).upper()

    def selectSaveFile(self):
        saveFilePath = os.getcwd()
        saveFilePathChoose, fileTypeFilter = QFileDialog.getSaveFileName(self,
                                                                         "Save File",
                                                                         saveFilePath,
                                                                         "Binary file (*.bin)")
        saveFilePath = os.path.abspath(saveFilePathChoose)
        if saveFilePathChoose == "":
            return (False, saveFilePath)
        return (True, saveFilePath)

    def exportNormalFirmware(self, filePath, saveFilePath):
        self.packing = True
        headFlagSize = 5
        sha256FlagSize = 32
        file_size = os.path.getsize(filePath)
        firmware_size = file_size - headFlagSize - sha256FlagSize
        if (firmware_size <= (0)):
            return False
        else:
            f = open(filePath, 'rb')
            headflag = f.read(headFlagSize)
            firmwareSizeflag = struct.unpack("I", headflag[1:5])[0]
            f.seek(headFlagSize)
            firmware = f.read(firmwareSizeflag)
            with open(saveFilePath, "wb") as f:
                f.write(firmware)
            return True

    def ConversionToNormalFirmware(self, filePath):
        if not os.path.exists(filePath):
            QMessageBox.warning(self, "文件转换错误",
                                "未选择固件文件，请选择之后重试", QMessageBox.Yes)
            # self.selectOpenFile(filePath)
            return
        # if not os.path.exists(filePath):
        #     return
        if self.fileType == FileType.TYPE_FIRMWARE:
            QMessageBox.warning(self, "转换为 K210 原始固件",
                                "固件为原始固件，无需转换", QMessageBox.Yes)
            return
        if self.fileType == FileType.TYPE_UNKNOWN:
            QMessageBox.warning(self, "转换为 K210 原始固件",
                                "非 K210 固件，请重新选择", QMessageBox.Yes)
            return
        flag, self.saveFilePath = self.selectSaveFile()
        print(flag, self.saveFilePath)
        if not flag:  # 用户取消保存
            return
        if not os.path.exists(os.path.dirname(self.saveFilePath)):
            QMessageBox.warning(self, "转换固件错误",
                                "未选择保存路径，请重新指定保存路径", QMessageBox.Yes)
            return
        # 文件转换
        if not self.saveFilePath.endswith(".bin"):
            self.saveFilePath += ".bin"
        # self.mergeBinFirmware(self.filePath, self.saveFilePath)
        flag = self.exportNormalFirmware(self.filePath, self.saveFilePath)
        if flag:
            QMessageBox.information(self, "转换为 K210 原始固件成功！",
                                    "固件保存路径：" + self.saveFilePath)
        else:
            QMessageBox.information(self, "转换为 K210 原始固件失败！",
                                    "文件大小错误")

    def mergeBinFirmware(self, filePath, saveFilePath):
        bin = b''
        aesFlag = b'\x00'

        size = os.path.getsize(filePath)
        fp = open(filePath, "rb")
        firmware = fp.read()
        fp.close()

        bin += aesFlag                # add aes key flag
        bin += struct.pack('I', size)  # add firmware length
        bin += firmware               # add firmware content
        sha256Hash = hashlib.sha256(bin).digest()
        # print("sha256Hash:" + str(binascii.b2a_hex(sha256Hash)))
        bin += sha256Hash             # add parity

        with open(saveFilePath, "wb") as f:
            f.write(bin)

    def ConversionToBurnFirmware(self, filePath):
        if not os.path.exists(filePath):
            QMessageBox.warning(self, "文件转换错误",
                                "未选择固件文件，请选择之后重试", QMessageBox.Yes)
            # self.selectOpenFile(filePath)
            return
        # if not os.path.exists(filePath):
        #     return

        if self.fileType == FileType.TYPE_UNKNOWN:
            QMessageBox.warning(self, "转换 FLASH 预烧录固件",
                                "未知文件类型，建议先检测固件类型是否为 K210 固件", QMessageBox.Yes)
            # return
        if self.fileType == FileType.TYPE_BURN_FIRMWARE:
            QMessageBox.warning(self, "转换 FLASH 预烧录固件",
                                "固件为 FLASH 预烧录固件，无需转换", QMessageBox.Yes)
            return

        flag, self.saveFilePath = self.selectSaveFile()
        print(flag, self.saveFilePath)
        if not flag:  # 用户取消保存
            return
        if not os.path.exists(os.path.dirname(self.saveFilePath)):
            QMessageBox.warning(self, "转换固件错误",
                                "未选择保存路径，请重新指定保存路径", QMessageBox.Yes)
            return
        # 文件转换
        if not self.saveFilePath.endswith(".bin"):
            self.saveFilePath += ".bin"
        self.mergeBinFirmware(self.filePath, self.saveFilePath)
        QMessageBox.information(self, "转换 FLASH 预烧录固件成功！",
                                "固件保存路径：" + self.saveFilePath)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    windows = MainWindows()
    windows.show()
    sys.exit(app.exec_())
