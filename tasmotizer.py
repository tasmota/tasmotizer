#!/usr/bin/env python

import sys

import serial

import tasmotizer_esptool as esptool
import json

from datetime import datetime

from PyQt5.QtCore import QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QTimer, QSize, QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QComboBox, QWidget, QCheckBox, QRadioButton, \
    QButtonGroup, QFileDialog, QProgressBar, QLabel, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout, QTabWidget, \
    QStatusBar

import banner

from gui import HLayout, VLayout, GroupBoxH, GroupBoxV, dark_palette
from sendconfig import SendConfigDialog


class StdOut(object):
    def __init__(self, processor):
        self.processor = processor

    def write(self, text):
        self.processor(text)

    def flush(self):
        pass


class ESPWorker(QObject):
    finished = pyqtSignal()
    port_error = pyqtSignal(str)
    backup_start = pyqtSignal()

    def __init__(self, port, bin_file, backup, erase):
        super().__init__()

        self.port = port
        self.bin_file = bin_file
        self.backup = backup
        self.erase = erase

        self.continue_flag = True

    @pyqtSlot()
    def execute(self):
        esptool.sw.setContinueFlag(True)
        command_base = ["--chip", "esp8266", "--port", self.port, "--baud", "115200"]
        command_backup = ["read_flash", "0x00000", "0x100000", "backup_{}.bin".format(datetime.now().strftime("%Y%m%d_%H%M%S"))]
        command_write = ["write_flash", "--flash_mode", "dout", "0x00000", self.bin_file]

        if self.erase:
            command_write.append("--erase-all")

        if self.backup and self.continue_flag:
            command = command_base + command_backup
            try:
                self.backup_start.emit()
                esptool.main(command)
            except esptool.FatalError or serial.SerialException as e:
                self.port_error.emit("{}".format(e))

        if self.continue_flag:
            command = command_base + command_write
            try:
                esptool.main(command)
                self.finished.emit()
            except esptool.FatalError or serial.SerialException as e:
                self.port_error.emit("{}".format(e))

    @pyqtSlot()
    def stop(self):
        self.continue_flag = False
        esptool.sw.setContinueFlag(False)


class FlashingDialog(QDialog):

    def __init__(self, parent):
        super().__init__()
        self.setWindowTitle("Tasmotizing...")

        esptool.sw.read_start.connect(self.read_start)
        esptool.sw.read_progress.connect(self.read_progress)
        esptool.sw.read_finished.connect(self.read_finished)

        esptool.sw.erase_start.connect(self.erase_start)
        esptool.sw.erase_finished.connect(self.erase_finished)

        esptool.sw.write_start.connect(self.write_start)
        esptool.sw.write_progress.connect(self.write_progress)
        esptool.sw.write_finished.connect(self.write_finished)

        self.setFixedWidth(400)

        self.nrBinFile = QNetworkRequest()
        self.parent = parent

        vl = VLayout(10, 10)
        self.setLayout(vl)

        self.bin_data = b""
        self.error_msg = None

        self.progress_task = QProgressBar()
        self.progress_task.setFixedHeight(45)
        self.task = QLabel()

        self.erase_timer = QTimer()
        self.erase_timer.setSingleShot(False)
        self.erase_timer.timeout.connect(self.erase_progress)

        self.btns = QDialogButtonBox(QDialogButtonBox.Abort)

        vl.addWidgets([QLabel("Tasmotizing in progress..."), self.task, self.progress_task, self.btns])

        self.btns.rejected.connect(self.abort)

        # process starts
        if parent.mode in (1, 2):
            self.bin_file = parent.cbHackboxBin.currentData().split(";")[1]
            self.nrBinFile.setUrl(QUrl(parent.cbHackboxBin.currentData().split(";")[0]))
            self.bin_reply = parent.nam.get(self.nrBinFile)
            self.task.setText("Downloading binary from thehackbox.org...")
            self.bin_reply.readyRead.connect(self.appendBinFile)
            self.bin_reply.downloadProgress.connect(self.updateBinProgress)
            self.bin_reply.finished.connect(self.saveBinFile)
        else:
            self.bin_file = parent.bin_file
            self.run_esptool()

    def appendBinFile(self):
        self.bin_data += self.bin_reply.readAll()

    def saveBinFile(self):
        if self.bin_reply.error() == QNetworkReply.NoError:
            with open(self.bin_file, "wb") as f:
                f.write(self.bin_data)
            self.progress_task.setValue(0)
            self.task.setText("Connecting to ESP...")
            self.run_esptool()
        else:
            QMessageBox.critical(self, "Network error", self.bin_reply.errorString())

    def updateBinProgress(self, recv, total):
        self.progress_task.setValue(recv//total*100)

    def read_start(self):
        self.progress_task.setValue(0)
        self.task.setText("Saving image backup...")

    def read_progress(self, value):
        self.progress_task.setValue(value)

    def read_finished(self):
        self.progress_task.setValue(100)
        self.task.setText("Writing done.")

    def erase_start(self):
        self.btns.setEnabled(False)
        self.progress_task.setValue(0)
        self.task.setText("Erasing flash... (this may take a while)")
        self.erase_timer.start(1000)

    def erase_progress(self):
        self.progress_task.setValue(self.progress_task.value()+5)

    def erase_finished(self):
        self.progress_task.setValue(100)
        self.task.setText("Erasing done.")
        self.erase_timer.stop()
        self.btns.setEnabled(True)

    def write_start(self):
        self.progress_task.setValue(0)
        self.task.setText("Writing image...")

    def write_progress(self, value):
        self.progress_task.setValue(value)

    def write_finished(self):
        self.progress_task.setValue(100)
        self.task.setText("Writing done.")
        self.accept()

    def run_esptool(self):
        self.espthread = QThread()
        self.espworker = ESPWorker(self.parent.cbxPort.currentData(), self.bin_file, self.parent.cbBackup.isChecked(),
                                   self.parent.cbErase.isChecked())

        self.espworker.port_error.connect(self.error)
        self.espworker.moveToThread(self.espthread)
        self.espthread.started.connect(self.espworker.execute)
        self.espthread.start()

    def abort(self):
        self.espworker.stop()
        self.espthread.quit()
        self.espthread.wait(2000)
        self.reject()

    def error(self, e):
        self.error_msg = e
        self.reject()

    def accept(self):
        self.espworker.stop()
        self.espthread.quit()
        self.espthread.wait(2000)
        self.done(QDialog.Accepted)


class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()
        self.settings = QSettings("tasmotizer.cfg", QSettings.IniFormat)
        self.sb = QStatusBar()

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/release/release.php"))
        self.nrDevelopment = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/development.php"))

        self.setWindowTitle("Tasmotizer 1.3")
        self.setMinimumWidth(480)

        self.mode = 0  # BIN file
        self.bin_file = ""

        self.release_data = b""
        self.development_data = b""

        self.createUI()

        self.refreshPorts()
        self.getHackBoxFeeds()

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)

        # Banner
        banner = QLabel()
        banner.setPixmap(QPixmap(":/banner.png"))
        vl.addWidget(banner)

        # Port groupbox
        gbPort = GroupBoxH("Select port", 3)
        self.cbxPort = QComboBox()
        pbRefreshPorts = QPushButton("Refresh")
        gbPort.addWidget(self.cbxPort)
        gbPort.addWidget(pbRefreshPorts)
        gbPort.layout().setStretch(0, 4)
        gbPort.layout().setStretch(1, 1)

        # Firmware groupbox
        gbFW = GroupBoxV("Select image", 3)

        hl_rb = HLayout(0)
        rbFile = QRadioButton("BIN file")
        self.rbRelease = QRadioButton("Release")
        self.rbRelease.setEnabled(False)
        self.rbDev = QRadioButton("Development")
        self.rbDev.setEnabled(False)

        rbgFW = QButtonGroup(gbFW)
        rbgFW.addButton(rbFile, 0)
        rbgFW.addButton(self.rbRelease, 1)
        rbgFW.addButton(self.rbDev, 2)

        hl_rb.addWidgets([rbFile, self.rbRelease, self.rbDev])
        gbFW.addLayout(hl_rb)

        self.wFile = QWidget()
        hl_file = HLayout(0)
        self.file = QLineEdit()
        self.file.setReadOnly(True)
        self.file.setPlaceholderText("Click 'Open' to select the image")
        pbFile = QPushButton("Open")
        hl_file.addWidgets([self.file, pbFile])
        self.wFile.setLayout(hl_file)

        self.cbHackboxBin = QComboBox()
        self.cbHackboxBin.setVisible(False)
        self.cbHackboxBin.setEnabled(False)

        self.cbBackup = QCheckBox("Backup original firmware")
        self.cbBackup.setToolTip("Firmware backup is ESPECIALLY recommended when you flash a Sonoff, Tuya, Shelly etc. for the first time.\nWithout a backup you won't be able to restore the original functionality.")

        self.cbErase = QCheckBox("Erase before flashing")
        self.cbErase.setToolTip("Erasing previous firmware ensures all flash regions are clean for Tasmota, which prevents many unexpected issues.\nIf unsure, leave enabled.")
        self.cbErase.setChecked(True)

        self.pbManualBackup = QPushButton("Backup")
        self.pbManualBackup.clicked.connect(self.backup)

        gbFW.addWidgets([self.wFile, self.cbHackboxBin])

        hl_backup = HLayout(0)
        hl_backup.addWidget(self.cbBackup)
        hl_backup.addSpacer()
        # hl_backup.addWidget(self.pbManualBackup)

        gbFW.addLayout(hl_backup)
        gbFW.addWidget(self.cbErase)

        # Buttons
        self.pbTasmotize = QPushButton("Tasmotize!")
        self.pbTasmotize.setFixedHeight(50)
        self.pbTasmotize.setStyleSheet("background-color: #223579;")

        self.pbConfig = QPushButton("Send config")
        self.pbConfig.setStyleSheet("background-color: #571054;")
        self.pbConfig.setFixedHeight(50)

        self.pbQuit = QPushButton("Quit")
        self.pbQuit.setStyleSheet("background-color: #c91017;")
        self.pbQuit.setFixedSize(QSize(50, 50))

        hl_btns = HLayout([50, 3, 50, 3])
        hl_btns.addWidgets([self.pbTasmotize, self.pbConfig, self.pbQuit])

        vl.addWidgets([gbPort, gbFW])
        vl.addLayout(hl_btns)
        vl.addWidget(self.sb)

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        rbgFW.buttonClicked[int].connect(self.setBinMode)
        rbFile.setChecked(True)
        pbFile.clicked.connect(self.openBinFile)

        self.pbTasmotize.clicked.connect(self.start_process)
        self.pbConfig.clicked.connect(self.send_config)
        self.pbQuit.clicked.connect(self.reject)

        self.sb.showMessage('Tasmotizer is ready!')

    def refreshPorts(self):
        self.cbxPort.clear()
        ports = reversed(sorted(port.portName() for port in QSerialPortInfo.availablePorts()))
        for p in ports:
            port = QSerialPortInfo(p)
            self.cbxPort.addItem(port.portName(), port.systemLocation())
        self.sb.showMessage('Refreshed ports list', 3000)

    def setBinMode(self, radio):
        self.mode = radio
        self.wFile.setVisible(self.mode == 0)
        self.cbHackboxBin.setVisible(self.mode > 0)

        if self.mode == 1:
            self.processReleaseInfo()
        elif self.mode == 2:
            self.processDevelopmentInfo()

    def getHackBoxFeeds(self):
        self.release_reply = self.nam.get(self.nrRelease)
        self.release_reply.readyRead.connect(self.appendReleaseInfo)
        self.release_reply.finished.connect(lambda: self.rbRelease.setEnabled(True))

        self.development_reply = self.nam.get(self.nrDevelopment)
        self.development_reply.readyRead.connect(self.appendDevelopmentInfo)
        self.development_reply.finished.connect(lambda: self.rbDev.setEnabled(True))

    def appendReleaseInfo(self):
        self.release_data += self.release_reply.readAll()

    def appendDevelopmentInfo(self):
        self.development_data += self.development_reply.readAll()

    def processReleaseInfo(self):
        reply = json.loads(str(self.release_data, 'utf8'))
        version, bins = list(reply.items())[0]
        self.rbRelease.setText("Release {}".format(version.lstrip("release-")))
        if len(bins) > 0:
            self.cbHackboxBin.clear()
            for img in bins:
                img['filesize'] //= 1024
                self.cbHackboxBin.addItem("{binary} [{filesize}kB]".format(**img), "{otaurl};{binary}".format(**img))
            self.cbHackboxBin.setEnabled(True)

    def processDevelopmentInfo(self):
        reply = json.loads(str(self.development_data, 'utf8'))
        _, cores = list(reply.items())[0]

        if len(cores) > 0:
            self.cbHackboxBin.clear()

            for core in list(cores.keys()):
                for img in cores[core]:
                    img['filesize'] //= 1024
                    self.cbHackboxBin.addItem("{binary} [{version}@{}, {commit}, {filesize}kB]".format(core, **img),
                                               "{otaurl};{}-dev-{version}-{commit}.bin".format(img['binary'].rstrip(".bin"), **img))
            self.cbHackboxBin.setEnabled(True)

    def openBinFile(self):
        previous_file = self.settings.value("bin_file")
        file, ok = QFileDialog.getOpenFileName(self, "Select Tasmota image", previous_file, filter="BIN files (*.bin)")
        if ok:
            self.file.setText(file)

    def send_config(self):
        dlg = SendConfigDialog()
        if dlg.exec_() == QDialog.Accepted:
            try:
                self.port = QSerialPort(self.cbxPort.currentData())
                self.port.setBaudRate(115200)
                self.port.open(QIODevice.ReadWrite)
                commands = f'backlog {";".join(dlg.commands)}'
                bytes_sent = self.port.write(bytes(commands, 'utf8'))
                QMessageBox.information(self, "Done",
                                        "Configuration sent ({} bytes)\nDevice will restart.".format(bytes_sent))
            except Exception as e:
                QMessageBox.critical(self, "Port error", e)

            finally:
                if self.port.isOpen():
                    self.port.close()

    def start_process(self):
        ok = True

        if self.mode == 0:
            if len(self.file.text()) > 0:
                self.bin_file = self.file.text()
                self.settings.setValue("bin_file", self.bin_file)

            else:
                ok = False
                QMessageBox.information(self, "Nothing to do...", "Select a local BIN file or select which one to download.")

        if ok:
            dlg = FlashingDialog(self)
            if dlg.exec_() == QDialog.Accepted:
                QMessageBox.information(self, "Done", "Flashing successful! Power cycle the device.")

            else:
                if dlg.error_msg:
                    QMessageBox.critical(self, "Error", dlg.error_msg)
                else:
                    QMessageBox.critical(self, "Flashing aborted", "Flashing process has been aborted by the user.")

    def backup(self):
        dlg = FlashingDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            QMessageBox.information(self, "Done", "Backup successful!")

    def mousePressEvent(self, e):
        self.old_pos = e.globalPos()

    def mouseMoveEvent(self, e):
        delta = e.globalPos() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = e.globalPos()


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle("Fusion")

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    app.setStyle("Fusion")

    mw = Tasmotizer()
    mw.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
