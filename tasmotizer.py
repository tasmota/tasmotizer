import os
import re
import sys
import esptool
import json

from datetime import datetime

from PyQt5.QtCore import QIODevice, QSize, QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QDialog, QLineEdit, QPushButton, QFormLayout, \
    QMainWindow, QGroupBox, QHBoxLayout, QVBoxLayout, QComboBox, QWidget, QSizePolicy, QCheckBox, QLabel, QRadioButton, \
    QButtonGroup, QFileDialog, QGroupBox, QSpinBox, QFrame, QStackedWidget, QPlainTextEdit, QListWidget, QProgressBar, \
    QLabel, QMessageBox

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


class VLayout(QVBoxLayout):
    def __init__(self, margin=3, spacing=3):
        super().__init__()
        if isinstance(margin, int):
            self.setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list):
            self.setContentsMargins(margin[0], margin[1], margin[2], margin[3])

        self.setSpacing(spacing)

    def addWidgets(self, widgets):
        for w in widgets:
            self.addWidget(w)

    def addSpacer(self):
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)


class HLayout(QHBoxLayout):
    def __init__(self, margin=3, spacing=3):
        super().__init__()
        if isinstance(margin, int):
            self.setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list):
            self.setContentsMargins(margin[0], margin[1], margin[2], margin[3])
        self.setSpacing(spacing)

    def addWidgets(self, widgets):
        for w in widgets:
            self.addWidget(w)

    def addSpacer(self):
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)


class GroupBoxV(QGroupBox):
    def __init__(self, title, margin=3, spacing=3, *args, **kwargs):
        super(GroupBoxV, self).__init__(*args, **kwargs)

        self.setTitle(title)

        layout = VLayout()
        layout.setSpacing(spacing)

        if isinstance(margin, int):
            layout.setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list):
            layout.setContentsMargins(margin[0], margin[1], margin[2], margin[3])

        self.setLayout(layout)

    def addWidget(self, w):
        self.layout().addWidget(w)

    def addWidgets(self, widgets):
        for w in widgets:
            self.layout().addWidget(w)

    def addLayout(self, w):
        self.layout().addLayout(w)


class GroupBoxH(QGroupBox):
    def __init__(self, title, margin=None, spacing=None, *args, **kwargs):
        super(GroupBoxH, self).__init__(title)
        self.setLayout(HLayout())

    def addWidget(self, w):
        self.layout().addWidget(w)

    def addWidgets(self, widgets):
        for w in widgets:
            self.layout().addWidget(w)

    def addLayout(self, w):
        self.layout().addLayout(w)


class SpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super(SpinBox, self).__init__(*args, **kwargs)
        self.setButtonSymbols(self.NoButtons)
        self.setMinimum(kwargs.get('minimum', 1))
        self.setMaximum(kwargs.get('maximum', 65535))


class ProgressWidget(QWidget):
    def __init__(self, label):
        super().__init__()
        self.setLayout(HLayout(0))
        self.progress = QProgressBar()
        self.layout().addWidgets([QLabel(label), self.progress])
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 1)

    def setValue(self, value):
        self.progress.setValue(value)


class StatusWidget(QWidget):
    def __init__(self, label):
        super().__init__()
        self.setLayout(HLayout(0))
        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        self.layout().addWidgets([QLabel(label), self.status])
        self.layout().setStretch(0, 1)
        self.layout().setStretch(1, 1)

    def setText(self, text):
        self.status.setText(text)


class StdOut(object):
    def __init__(self, processor):
        self.processor = processor

    def write(self, text):
        self.processor(text)

    def flush(self):
        pass


class ESPWorker(QObject):
    finished = pyqtSignal()
    port_error = pyqtSignal()

    def __init__(self, port, bin_file, backup, erase):
        super().__init__()

        self.port = port
        self.bin_file = bin_file
        self.backup = backup
        self.erase = erase

    @pyqtSlot()
    def execute(self):
        command_base = ["--chip", "esp8266", "--port", self.port, "--baud", "115200"]
        command_backup = ["--after", "no_reset", "read_flash", "0x00000", "0x100000",
                          "backup_{}.bin".format(datetime.now().strftime("%Y%m%d_%H%M%S"))]
        command_write = ["--after", "no_reset", "write_flash", "--flash_mode", "dout", "0x00000", self.bin_file]

        if self.erase:
            command_write.append("--erase-all")

        if self.backup:
            command = command_base + command_backup
            try:
                esptool.main(command)
            except esptool.FatalError as e:
                self.port_error.emit()

        command = command_base + command_write
        try:
            esptool.main(command)
        except esptool.FatalError as e:
            self.port_error.emit()

        self.finished.emit()


class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/release/release.php"))
        self.nrDevelopment = QNetworkRequest(QUrl("http://thehackbox.org/tasmota/development.php"))
        self.nrBinFile = QNetworkRequest()

        self.setWindowTitle("Tasmotizer")
        self.setFixedSize(QSize(800, 800/1.68))

        self.mode = 0  # BIN file
        self.module_mode = 0  # Module
        self.bin_file = None

        self.release_data = b""
        self.development_data = b""
        self.template_data = b""
        self.bin_data = b""

        vl_stack = VLayout(0)
        self.stack = QStackedWidget()
        vl_stack.addWidget(self.stack)
        self.setLayout(vl_stack)

        # Main page
        self.wMainPage = QWidget()
        self.createMainPage()
        self.stack.addWidget(self.wMainPage)

        # Progress page
        self.wProgressPage = QWidget()
        self.createProgressPage()
        self.stack.addWidget(self.wProgressPage)

        self.refreshPorts()
        self.getHackBoxFeeds()

        self.console = QListWidget()
        self.console.setMinimumWidth(800)
        self.console.show()

        self.port = QSerialPort("ttyUSB0")
        self.port.setBaudRate(115200)

    def createMainPage(self):
        hl_main = HLayout()
        vl_main_left = VLayout(0)
        vl_main_right = VLayout(0)
        hl_main.addLayout(vl_main_left)
        hl_main.addLayout(vl_main_right)

        # Port groupbox
        gbPort = GroupBoxH("Select port")
        self.cbxPort = QComboBox()
        pbRefreshPorts = QPushButton("Refresh")
        gbPort.addWidget(self.cbxPort)
        gbPort.addWidget(pbRefreshPorts)
        gbPort.layout().setStretch(0, 4)
        gbPort.layout().setStretch(1, 1)

        # Firmware groupbox
        gbFW = GroupBoxV("Select image")

        hl_rb = HLayout()
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

        # Wifi groupbox
        self.gbWifi = QGroupBox("WiFi")
        self.gbWifi.setCheckable(True)
        self.gbWifi.setChecked(False)
        flWifi = QFormLayout()
        self.leAP = QLineEdit()
        self.leAPPwd = QLineEdit()
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

        # MQTT groupbox
        self.gbMQTT = QGroupBox("MQTT")
        self.gbMQTT.setCheckable(True)
        self.gbMQTT.setChecked(False)
        flMQTT = QFormLayout()
        self.leBroker = QLineEdit()
        self.sbPort = SpinBox()
        self.sbPort.setValue(1883)
        self.leTopic = QLineEdit()
        self.leMQTTUser = QLineEdit()
        self.leMQTTPass = QLineEdit()
        flMQTT.addRow("Host", self.leBroker)
        flMQTT.addRow("Port", self.sbPort)
        flMQTT.addRow("Topic", self.leTopic)
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

        rbgModule = QButtonGroup(gbFW)
        rbgModule.addButton(self.rbModule, 0)
        rbgModule.addButton(self.rbTemplate, 1)

        self.cbModule = QComboBox()
        for mod_id, mod_name in modules.items():
            self.cbModule.addItem(mod_name, mod_id)

        self.leTemplate = QLineEdit()
        self.leTemplate.setVisible(False)

        self.gbModule.addLayout(hl_m_rb)
        self.gbModule.addWidgets([self.cbModule, self.leTemplate])

        # add all widgets to main layout
#         vl_main_left.addWidgets([gbPort, gbFW, self.gbWifi, self.gbRecWifi, self.gbMQTT, self.gbModule])
        vl_main_left.addWidgets([gbPort, gbFW, self.gbWifi, self.gbRecWifi])
        vl_main_right.addWidgets([self.gbMQTT, self.gbModule])

        # Tasmotize button
        self.pbTasmotize = QPushButton("Tasmotize!")
        self.pbTasmotize.setFixedHeight(50)
        hl_tasmotize = HLayout([50, 3, 50, 3])
        hl_tasmotize.addWidget(self.pbTasmotize)

        vl_main_left.addStretch(1)
        vl_main_left.addLayout(hl_tasmotize)

        vl_main_right.addStretch(1)
        hl_main.setStretch(0, 1)
        hl_main.setStretch(1, 1)

#         self.wMainPage.setLayout(vl_main_left)
        self.wMainPage.setLayout(hl_main)

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        rbgFW.buttonClicked[int].connect(self.setBinMode)
        rbgModule.buttonClicked[int].connect(self.setModuleMode)
        rbFile.setChecked(True)
        pbFile.clicked.connect(self.openBinFile)
        self.pbTasmotize.clicked.connect(self.stage1)

    def createProgressPage(self):
        vl = VLayout()

        self.download_progress = ProgressWidget("Downloading image")

        self.connection_status = StatusWidget("ESP8266 connection")
        self.connection_status.setVisible(False)

        self.backup_progress = ProgressWidget("Saving backup")
        self.backup_progress.setVisible(False)

        self.erase_status = StatusWidget("Erasing flash...")
        self.erase_status.setVisible(False)

        self.flash_progress = ProgressWidget("Flashing")
        self.flash_progress.setVisible(False)

        self.flashing_status = StatusWidget("Flashing complete! Restart device.")
        self.flashing_status.setVisible(False)

        vl.addWidgets([self.download_progress, self.connection_status, self.backup_progress, self.erase_status, self.flash_progress, self.flashing_status])

        vl.addStretch(1)
        self.wProgressPage.setLayout(vl)

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

    def setModuleMode(self, radio):
        self.module_mode = radio
        self.cbModule.setVisible(not radio)
        self.leTemplate.setVisible(radio)

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

    def appendBinFile(self):
        self.bin_data += self.bin_reply.readAll()

    def saveBinFile(self):
        if self.bin_reply.error() == QNetworkReply.NoError:
            with open(self.bin_file, "wb") as f:
                f.write(self.bin_data)
            self.stage2()
        else:
            self.stack.setCurrentIndex(0)
            QMessageBox.critical(self, "Network error", self.bin_reply.errorString())

    def updateBinProgress(self, recv, total):
        self.download_progress.setValue(recv//total*100)

    def processStdOut(self, text):
        text = text.strip("\n")
        if len(text) > 0:
            self.console.addItem(QListWidgetItem(text))

        if text.startswith("Chip is"):
            self.connection_status.setText("OK")

        elif text.startswith("Erasing flash"):
            self.erase_status.setVisible(True)

        elif text.startswith("Chip erase completed"):
            self.erase_status.setText("Done")

        backup_mtch = re.match(r"\d+ \((\d+) %\)", text)
        if backup_mtch:
            if not self.backup_progress.isVisible():
                self.backup_progress.setVisible(True)
            percent = int(backup_mtch.groups()[0])
            self.backup_progress.setValue(percent)

        flash_mtch = re.match(r"[\r]Writing at 0x[0-9a-fA-F]+\.\.\. \((\d+) %\)", text)
        if flash_mtch:
            if not self.flash_progress.isVisible():
                self.flash_progress.setVisible(True)
            percent = int(flash_mtch.groups()[0])
            self.flash_progress.setValue(percent)

    def process_serial(self):
        try:
            s = str(self.port.readAll(), 'ascii').strip()
            print(s)
            if re.findall(r"192.168.4.1", s):
                print('found')
                self.stage4()

        except:
            pass

    def stage1(self):
        ok = True

        if self.gbWifi.isChecked() and not (self.leAP.text() or self.leAPPwd.text()):
            ok = False
            QMessageBox.warning(self, "WiFi details incomplete", "Input WiFi AP and Password")

        if self.gbMQTT.isChecked() and not self.leBroker.text():
            ok = False
            QMessageBox.warning(self, "MQTT details incomplete", "Input broker hostname")

        if ok:
            if self.mode == 0:
                if len(self.file.text()) > 0:
                    self.bin_file = self.file.text()
                    self.stage2()
                else:
                    QMessageBox.information(self, "Nothing to do...", "Select a local BIN file or select which one to download.")

            elif self.mode in (1, 2):
                self.download_progress.setVisible(True)
                self.bin_file = self.cbHackboxBin.currentData().split(";")[1]
                self.nrBinFile.setUrl(QUrl(self.cbHackboxBin.currentData().split(";")[0]))
                self.bin_reply = self.nam.get(self.nrBinFile)
                self.bin_reply.readyRead.connect(self.appendBinFile)
                self.bin_reply.downloadProgress.connect(self.updateBinProgress)
                self.bin_reply.finished.connect(self.saveBinFile)

    def stage2(self):
        sys.stdout = StdOut(self.processStdOut)
        self.stack.setCurrentIndex(1)

        self.espthread = QThread()
        self.espworker = ESPWorker(self.cbxPort.currentText(), self.bin_file, self.cbBackup.isChecked(),
                                   self.cbErase.isChecked())

        self.espworker.finished.connect(self.stage3)
        self.espworker.port_error.connect(lambda: print("error"))

        self.espworker.moveToThread(self.espthread)
        self.espthread.started.connect(self.espworker.execute)
        self.espthread.start()
        self.connection_status.setVisible(True)

    def stage3(self):
        if self.gbWifi.isChecked() or self.gbMQTT.isChecked():
            self.flashing_status.setVisible(True)
            self.port.open(QIODevice.ReadWrite)
            self.port.readyRead.connect(self.process_serial)
        else:
            self.stack.setCurrentIndex(0)
            QMessageBox.information(self, "Done", "Flashing successful!")

    def stage4(self):
        backlog = []

        if self.gbWifi.isChecked():
            backlog.extend(["ssid1 {}".format(self.leAP.text()), "password1 {}".format(self.leAPPwd.text())])

        if self.gbRecWifi.isChecked():
            backlog.extend(["ssid2 Recovery", "password2 a1b2c3d4"])

        if self.gbMQTT.isChecked():
            backlog.extend(["mqtthost {}".format(self.leBroker.text()), "mqttport {}".format(self.sbPort.value())])

            topic = self.leTopic.text()
            if topic:
                backlog.append("topic {}".format(topic))

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
                backlog.extend(["template {}".format(self.leTemplate.text), "module 0"])


        commands = "backlog {}\n".format(";".join(backlog))
        print(commands)
        print(self.port.write(bytes(commands, 'utf8')))
        self.stack.setCurrentIndex(0)
        QMessageBox.information(self, "Done", "Flashing and configuration successful!")

    def closeEvent(self, e):
        self.console.close()
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

    # app.setPalette(dark_palette)
    # app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    mw = Tasmotizer()
    mw.show()

    sys.exit(app.exec_())
