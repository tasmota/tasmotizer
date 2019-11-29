import os
import re
import sys
import esptool
import json

from datetime import datetime

import serial
from PyQt5.QtCore import QIODevice, QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QSize, QTimer, QTimer
from PyQt5.QtGui import QPalette, QColor, QPixmap
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QListWidgetItem, QDialog, QLineEdit, QPushButton, QFormLayout, QComboBox, \
    QWidget, QCheckBox, QRadioButton, QButtonGroup, QFileDialog, QGroupBox, QStackedWidget, QListWidget, QProgressBar, \
    QLabel, QMessageBox, QDialogButtonBox

from gui import HLayout, VLayout, GroupBoxH, GroupBoxV

modules = {"1": "Sonoff Basic", "2": "Sonoff RF", "4": "Sonoff TH", "5": "Sonoff Dual", "39": "Sonoff Dual R2",
           "6": "Sonoff Pow", "43": "Sonoff Pow R2", "7": "Sonoff 4CH", "23": "Sonoff 4CH Pro", "41": "Sonoff S31",
           "8": "Sonoff S2X", "10": "Sonoff Touch", "28": "Sonoff T1 1CH", "29": "Sonoff T1 2CH", "30": "Sonoff T1 3CH",
           "11": "Sonoff LED", "22": "Sonoff BN-SZ", "70": "Sonoff L1", "26": "Sonoff B1", "9": "Slampher",
           "21": "Sonoff SC", "44": "Sonoff iFan02", "71": "Sonoff iFan03", "25": "Sonoff Bridge", "3": "Sonoff SV",
           "19": "Sonoff Dev", "12": "1 Channel", "13": "4 Channel", "14": "Motor C/AC", "15": "ElectroDragon",
           "16": "EXS Relay(s)", "31": "Supla Espablo", "35": "Luani HVIO", "33": "Yunshan Relay", "17": "WiOn",
           "46": "Shelly 1", "47": "Shelly 2", "45": "BlitzWolf SHP", "52": "Teckin", "59": "Teckin US",
           "53": "AplicWDP303075", "55": "Gosund SP1 v23", "65": "Luminea ZX2820", "57": "SK03 Outdoor",
           "63": "Digoo DG-SP202", "64": "KA10", "67": "SP10", "68": "WAGA CHCZ02MB", "49": "Neo Coolcam",
           "51": "OBI Socket", "61": "OBI Socket 2", "60": "Manzoku strip", "50": "ESP Switch", "54": "Tuya MCU",
           "56": "ARMTR Dimmer", "58": "PS-16-DZ", "20": "H801", "34": "MagicHome", "37": "Arilux LC01",
           "40": "Arilux LC06", "38": "Arilux LC11", "42": "Zengge WF017", "24": "Huafan SS", "36": "KMC 70011",
           "27": "AiLight", "48": "Xiaomi Philips", "69": "SYF05", "62": "YTF IR Bridge", "32": "Witty Cloud",
           "18": "Generic"}

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
        command_backup = ["--after", "no_reset", "read_flash", "0x00000", "0x100000",
                          "backup_{}.bin".format(datetime.now().strftime("%Y%m%d_%H%M%S"))]
        command_write = ["--after", "no_reset", "write_flash", "--flash_mode", "dout", "0x00000", self.bin_file]

        if self.erase:
            command_write.append("--erase-all")

        if self.backup and self.continue_flag:
            command = command_base + command_backup
            try:
                self.backup_start.emit()
                esptool.main(command)
            except Exception as e:
            # except esptool.FatalError or serial.SerialException as e:
                self.port_error.emit("{}".format(e))

        if self.continue_flag:
            command = command_base + command_write
            try:
                esptool.main(command)
                self.finished.emit()
            except Exception as e:
            # except esptool.FatalError or serial.SerialException as e:
                self.port_error.emit("{}".format(e))

    @pyqtSlot()
    def stop(self):
        self.continue_flag = False
        esptool.sw.setContinueFlag(False)


class FlashingDialog(QDialog):

    def __init__(self, parent):
        super().__init__()

        esptool.sw.read_start.connect(self.read_start)
        esptool.sw.read_progress.connect(self.read_progress)
        esptool.sw.read_finished.connect(self.read_finished)

        esptool.sw.erase_start.connect(self.erase_start)
        esptool.sw.erase_finished.connect(self.erase_finished)

        esptool.sw.write_start.connect(self.write_start)
        esptool.sw.write_progress.connect(self.write_progress)
        esptool.sw.write_finished.connect(self.write_finished)
        
        self.setWindowFlag(Qt.FramelessWindowHint | Qt.ApplicationModal)
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

        btns = QDialogButtonBox(QDialogButtonBox.Abort)

        vl.addWidgets([QLabel("Tasmotizing in progress..."), self.task, self.progress_task, btns])

        btns.rejected.connect(self.abort)

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

    def processStdOut(self, text):
        text = text.strip("\n")
        # if len(text) > 0:
        #     self.parent.console.addItem(QListWidgetItem(text))

        if text.startswith("Erasing"):
            self.progress_task.setValue(0)
            self.task.setText("Erasing flash... (this may take a while)")
            self.erase_start.emit()

        if text in ("_", "."):
            self.progress_task.setValue(self.progress_task.value()+1)

        backup_mtch = re.match(r"\d+ \((\d+) %\)", text)
        if backup_mtch:
            percent = int(backup_mtch.groups()[0])
            self.progress_task.setValue(percent)

        flash_mtch = re.match(r"[\r]Writing at 0x[0-9a-fA-F]+\.\.\. \((\d+) %\)", text)
        if flash_mtch:
            self.write_start.emit()
            percent = int(flash_mtch.groups()[0])
            self.progress_task.setValue(percent)

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
        self.progress_task.setValue(0)
        self.task.setText("Erasing flash... (this may take a while)")
        self.erase_timer.start(1000)

    def erase_progress(self):
        self.progress_task.setValue(self.progress_task.value()+5)

    def erase_finished(self):
        self.progress_task.setValue(100)
        self.task.setText("Erasing done.")
        self.erase_timer.stop()

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
        # sys.stdout = StdOut(self.processStdOut)
        self.espthread = QThread()
        self.espworker = ESPWorker(self.parent.cbxPort.currentText(), self.bin_file, self.parent.cbBackup.isChecked(),
                                   self.parent.cbErase.isChecked())

        self.espworker.port_error.connect(self.error)
        self.espworker.moveToThread(self.espthread)
        self.espthread.started.connect(self.espworker.execute)
        self.espthread.start()
        # self.settings.setValue("bin_file", self.bin_file)

    def abort(self):
        self.espworker.stop()
        self.espthread.quit()
        self.espthread.wait(2000)
        del self.espworker
        del self.espthread
        self.reject()

    def error(self, e):
        self.error_msg = e
        self.reject()

    def accept(self):
        self.espworker.stop()
        self.espthread.quit()
        self.espthread.wait(2000)
        del self.espworker
        del self.espthread
        self.done(QDialog.Accepted)


class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()
        self.settings = QSettings("tasmotizer.cfg", QSettings.IniFormat)

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/release/release.php"))
        self.nrDevelopment = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/development.php"))

        self.setWindowTitle("Tasmotizer")
        self.setMinimumWidth(480)

        self.mode = 0  # BIN file
        self.bin_file = ""

        self.release_data = b""
        self.development_data = b""

        # Main page
        self.createUI()

        self.refreshPorts()
        self.getHackBoxFeeds()

        # self.console = QListWidget()
        # self.console.setMinimumWidth(800)
        # self.console.show()

        # self.port = QSerialPort("ttyUSB0")
        # self.port.setBaudRate(115200)

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)

        # Banner
        banner = QLabel()
        banner.setPixmap(QPixmap("banner.png"))
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
        self.cbErase = QCheckBox("Erase before flashing")
        self.cbErase.setChecked(True)

        gbFW.addWidgets([self.wFile, self.cbHackboxBin, self.cbBackup, self.cbErase])

        # Buttons
        self.pbTasmotize = QPushButton("Tasmotize!")
        self.pbTasmotize.setFixedHeight(50)
        # self.pbTasmotize.setStyleSheet("background-color: #1fa3ec;")
        self.pbTasmotize.setStyleSheet("background-color: #223579;")

        self.pbConfig = QPushButton("Send config")
        self.pbConfig.setStyleSheet("background-color: #571054;")
        # self.pbConfig.setStyleSheet("background-color: #d43535;")
        self.pbConfig.setFixedHeight(50)

        hl_btns = HLayout([50, 3, 50, 3])
        hl_btns.addWidgets([self.pbTasmotize, self.pbConfig])

        vl.addWidgets([gbPort, gbFW])
        vl.addLayout(hl_btns)

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        rbgFW.buttonClicked[int].connect(self.setBinMode)
        rbFile.setChecked(True)
        pbFile.clicked.connect(self.openBinFile)

        self.pbTasmotize.clicked.connect(self.start_process)

    def refreshPorts(self):
        self.cbxPort.clear()
        ports = reversed(sorted(port.portName() for port in QSerialPortInfo.availablePorts()))
        for p in ports:
            port = QSerialPortInfo(p)
            self.cbxPort.addItem("{}".format(port.systemLocation()))

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
        file, ok = QFileDialog.getOpenFileName(self, "Select Tasmota image", filter="BIN files (*.bin)")
        if ok:
            self.file.setText(file)

    def start_process(self):
        ok = True

        if self.mode == 0:
            if len(self.file.text()) > 0:
                self.bin_file = self.file.text()

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

            del dlg


        # ok = True
        #
        # if self.gbWifi.isChecked() and not (self.leAP.text() or self.leAPPwd.text()):
        #     ok = False
        #     QMessageBox.warning(self, "WiFi details incomplete", "Input WiFi AP and Password")
        #
        # if self.gbMQTT.isChecked() and not self.leBroker.text():
        #     ok = False
        #     QMessageBox.warning(self, "MQTT details incomplete", "Input broker hostname")
        #
        # if ok:

    # def stage4(self):
    #     backlog = []
    #
    #     if self.gbWifi.isChecked():
    #         backlog.extend(["ssid1 {}".format(self.leAP.text()), "password1 {}".format(self.leAPPwd.text())])
    #
    #     if self.gbRecWifi.isChecked():
    #         backlog.extend(["ssid2 Recovery", "password2 a1b2c3d4"])
    #
    #     if self.gbMQTT.isChecked():
    #         backlog.extend(["mqtthost {}".format(self.leBroker.text()), "mqttport {}".format(self.sbPort.value())])
    #
    #         topic = self.leTopic.text()
    #         if topic:
    #             backlog.append("topic {}".format(topic))
    #
    #         mqttuser = self.leMQTTUser.text()
    #         if mqttuser:
    #             backlog.append("mqttuser {}".format(mqttuser))
    #
    #             mqttpassword = self.leMQTTPass.text()
    #             if mqttpassword:
    #                 backlog.append("mqttpassword {}".format(mqttpassword))
    #
    #     if self.gbModule.isChecked():
    #         if self.module_mode == 0:
    #             backlog.append("module {}".format(self.cbModule.currentData()))
    #
    #         elif self.module_mode == 1:
    #             backlog.extend(["template {}".format(self.leTemplate.text), "module 0"])
    #
    #
    #     commands = "backlog {}\n".format(";".join(backlog))
    #     print(commands)
    #     print(self.port.write(bytes(commands, 'utf8')))
    #     self.stack.setCurrentIndex(0)
    #     QMessageBox.information(self, "Done", "Flashing and configuration successful!")

    def closeEvent(self, e):
        self.settings.setValue("mode", self.mode)
        self.settings.sync()
        # self.console.close()
        e.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    app.setStyle("Fusion")

    dark_palette = QPalette()

    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    mw = Tasmotizer()
    mw.show()

    sys.exit(app.exec_())
