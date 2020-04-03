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
    QButtonGroup, QFileDialog, QProgressBar, QLabel, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout

import banner

from gui import HLayout, VLayout, GroupBoxH, GroupBoxV, SpinBox, dark_palette

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
        command_backup = ["read_flash", "0x00000", "0x100000", "backup_{}.bin".format(datetime.now().strftime("%Y%m%d_%H%M%S"))]
        command_write = ["write_flash", "--flash_size", "1MB", "--flash_mode", "dout", "0x00000", self.bin_file]

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


class SendConfigDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(640)
        self.setWindowTitle("Send configuration to device")
        self.settings = QSettings("tasmotizer.cfg", QSettings.IniFormat)

        self.commands = None
        self.module_mode = 0

        self.createUI()
        self.loadSettings()

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)

        # Wifi groupbox
        self.gbWifi = QGroupBox("WiFi")
        self.gbWifi.setCheckable(True)
        self.gbWifi.setChecked(False)
        flWifi = QFormLayout()
        self.leAP = QLineEdit()
        self.leAPPwd = QLineEdit()
        self.leAPPwd.setEchoMode(QLineEdit.Password)
        flWifi.addRow("SSID", self.leAP)
        flWifi.addRow("Password", self.leAPPwd)
        self.gbWifi.setLayout(flWifi)

        # Recovery Wifi groupbox
        self.gbRecWifi = QGroupBox("Recovery WiFi")
        self.gbRecWifi.setCheckable(True)
        self.gbRecWifi.setChecked(False)
        flRecWifi = QFormLayout()
        lbRecAP = QLabel("Recovery")
        lbRecAP.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        lbRecAPPwd = QLabel("a1b2c3d4")
        lbRecAPPwd.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        flRecWifi.addRow("SSID", lbRecAP)
        flRecWifi.addRow("Password", lbRecAPPwd)
        self.gbRecWifi.setLayout(flRecWifi)

        vl_wifis = VLayout(0)
        vl_wifis.addWidgets([self.gbWifi, self.gbRecWifi])

        # MQTT groupbox
        self.gbMQTT = QGroupBox("MQTT")
        self.gbMQTT.setCheckable(True)
        self.gbMQTT.setChecked(False)
        flMQTT = QFormLayout()
        self.leBroker = QLineEdit()
        self.sbPort = SpinBox()
        self.sbPort.setValue(1883)
        self.leTopic = QLineEdit()
        self.leTopic.setText("tasmota")
        self.leFullTopic = QLineEdit()
        self.leFullTopic.setText("%prefix%/%topic%/")
        self.leFriendlyName = QLineEdit()
        self.leMQTTUser = QLineEdit()
        self.leMQTTPass = QLineEdit()
        self.leMQTTPass.setEchoMode(QLineEdit.Password)

        flMQTT.addRow("Host", self.leBroker)
        flMQTT.addRow("Port", self.sbPort)
        flMQTT.addRow("Topic", self.leTopic)
        flMQTT.addRow("FullTopic", self.leFullTopic)
        flMQTT.addRow("FriendlyName", self.leFriendlyName)
        flMQTT.addRow("User [optional]", self.leMQTTUser)
        flMQTT.addRow("Password [optional]", self.leMQTTPass)
        self.gbMQTT.setLayout(flMQTT)

        # Module/template groupbox
        self.gbModule = GroupBoxV("Module/template")
        self.gbModule.setCheckable(True)
        self.gbModule.setChecked(False)

        hl_m_rb = HLayout()
        self.rbModule = QRadioButton("Module")
        self.rbModule.setChecked(True)
        self.rbTemplate = QRadioButton("Template")
        hl_m_rb.addWidgets([self.rbModule, self.rbTemplate])

        self.rbgModule = QButtonGroup(self.gbModule)
        self.rbgModule.addButton(self.rbModule, 0)
        self.rbgModule.addButton(self.rbTemplate, 1)

        self.cbModule = QComboBox()
        for mod_id, mod_name in modules.items():
            self.cbModule.addItem(mod_name, mod_id)

        self.leTemplate = QLineEdit()
        self.leTemplate.setPlaceholderText("Paste template string here")
        self.leTemplate.setVisible(False)

        self.gbModule.addLayout(hl_m_rb)
        self.gbModule.addWidgets([self.cbModule, self.leTemplate])
        self.rbgModule.buttonClicked[int].connect(self.setModuleMode)

        # layout all widgets
        hl_wifis_mqtt = HLayout(0)
        hl_wifis_mqtt.addLayout(vl_wifis)
        hl_wifis_mqtt.addWidget(self.gbMQTT)

        vl.addLayout(hl_wifis_mqtt)
        vl.addWidget(self.gbModule)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

    def loadSettings(self):
        self.gbWifi.setChecked(self.settings.value("gbWifi", False, bool))
        self.leAP.setText(self.settings.value("AP"))

        self.gbRecWifi.setChecked(self.settings.value("gbRecWifi", False, bool))

        self.gbMQTT.setChecked(self.settings.value("gbMQTT", False, bool))
        self.leBroker.setText(self.settings.value("Broker"))
        self.sbPort.setValue(self.settings.value("Port", 1883, int))
        self.leTopic.setText(self.settings.value("Topic", "tasmota"))
        self.leFullTopic.setText(self.settings.value("FullTopic", "%prefix%/%topic%/"))
        self.leFriendlyName.setText(self.settings.value("FriendlyName"))
        self.leMQTTUser.setText(self.settings.value("MQTTUser"))

        self.gbModule.setChecked(self.settings.value("gbModule", False, bool))

        module_mode = self.settings.value("ModuleMode", 0, int)
        for b in self.rbgModule.buttons():
            if self.rbgModule.id(b) == module_mode:
                b.setChecked(True)
                self.setModuleMode(module_mode)
        self.cbModule.setCurrentText(self.settings.value("Module", "Generic"))
        self.leTemplate.setText(self.settings.value("Template"))

    def setModuleMode(self, radio):
        self.module_mode = radio
        self.cbModule.setVisible(not radio)
        self.leTemplate.setVisible(radio)

    def accept(self):
        ok = True

        if self.gbWifi.isChecked() and (len(self.leAP.text()) == 0 or len(self.leAPPwd.text()) == 0):
            ok = False
            QMessageBox.warning(self, "WiFi details incomplete", "Input WiFi AP and Password")

        if self.gbMQTT.isChecked() and not self.leBroker.text():
            ok = False
            QMessageBox.warning(self, "MQTT details incomplete", "Input broker hostname")

        if self.module_mode == 1 and len(self.leTemplate.text()) == 0:
            ok = False
            QMessageBox.warning(self, "Template string missing", "Input template string")

        if ok:
            backlog = []

            if self.gbWifi.isChecked():
                backlog.extend(["ssid1 {}".format(self.leAP.text()), "password1 {}".format(self.leAPPwd.text())])

            if self.gbRecWifi.isChecked():
                backlog.extend(["ssid2 Recovery", "password2 a1b2c3d4"])

            if self.gbMQTT.isChecked():
                backlog.extend(["mqtthost {}".format(self.leBroker.text()), "mqttport {}".format(self.sbPort.value())])

                topic = self.leTopic.text()
                if topic and topic != "tasmota":
                    backlog.append("topic {}".format(topic))

                fulltopic = self.leFullTopic.text()
                if fulltopic and fulltopic != "%prefix%/%topic%/":
                    backlog.append("fulltopic {}".format(fulltopic))

                fname = self.leFriendlyName.text()
                if fname:
                    backlog.append("friendlyname {}".format(fname))

                mqttuser = self.leMQTTUser.text()
                if mqttuser:
                    backlog.append("mqttuser {}".format(mqttuser))

                    mqttpassword = self.leMQTTPass.text()
                    if mqttpassword:
                        backlog.append("mqttpassword {}".format(mqttpassword))

            if self.gbModule.isChecked():
                if self.module_mode == 0:
                    backlog.append("module {}".format(self.cbModule.currentData()))

                elif self.module_mode == 1:
                    backlog.extend(["template {}".format(self.leTemplate.text()), "module 0"])

            self.commands = "backlog {}\n".format(";".join(backlog))

            self.done(QDialog.Accepted)


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

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/release/release.php"))
        self.nrDevelopment = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/development.php"))

        self.setWindowTitle("Tasmotizer 1.1a")
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

        gbFW.addWidgets([self.wFile, self.cbHackboxBin, self.cbBackup, self.cbErase])

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

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        rbgFW.buttonClicked[int].connect(self.setBinMode)
        rbFile.setChecked(True)
        pbFile.clicked.connect(self.openBinFile)

        self.pbTasmotize.clicked.connect(self.start_process)
        self.pbConfig.clicked.connect(self.send_config)
        self.pbQuit.clicked.connect(self.reject)

    def refreshPorts(self):
        self.cbxPort.clear()
        ports = reversed(sorted(port.portName() for port in QSerialPortInfo.availablePorts()))
        for p in ports:
            port = QSerialPortInfo(p)
            self.cbxPort.addItem(port.portName(), port.systemLocation())

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
            if dlg.commands:
                try:
                    self.port = QSerialPort(self.cbxPort.currentData())
                    self.port.setBaudRate(115200)
                    self.port.open(QIODevice.ReadWrite)
                    bytes_sent = self.port.write(bytes(dlg.commands, 'utf8'))
                except Exception as e:
                    QMessageBox.critical(self, "Port error", e)
                else:
                    self.settings.setValue("gbWifi", dlg.gbWifi.isChecked())
                    self.settings.setValue("AP", dlg.leAP.text())

                    self.settings.setValue("gbRecWifi", dlg.gbRecWifi.isChecked())

                    self.settings.setValue("gbMQTT", dlg.gbMQTT.isChecked())
                    self.settings.setValue("Broker", dlg.leBroker.text())
                    self.settings.setValue("Port", dlg.sbPort.value())
                    self.settings.setValue("Topic", dlg.leTopic.text())
                    self.settings.setValue("FullTopic", dlg.leFullTopic.text())
                    self.settings.setValue("FriendlyName", dlg.leFriendlyName.text())
                    self.settings.setValue("MQTTUser", dlg.leMQTTUser.text())

                    self.settings.setValue("gbModule", dlg.gbModule.isChecked())
                    self.settings.setValue("ModuleMode", dlg.rbgModule.checkedId())
                    self.settings.setValue("Module", dlg.cbModule.currentText())
                    self.settings.setValue("Template", dlg.leTemplate.text())
                    self.settings.sync()

                    QMessageBox.information(self, "Done", "Configuration sent ({} bytes)\nDevice will restart.".format(bytes_sent))
                finally:
                    if self.port.isOpen():
                        self.port.close()
            else:
                QMessageBox.information(self, "Done", "Nothing to send")

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
