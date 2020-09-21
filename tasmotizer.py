#!/usr/bin/env python
import re
import sys
from time import sleep

import serial

import tasmotizer_esptool as esptool
import json

from datetime import datetime

from PyQt5.QtCore import QUrl, Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSettings, QTimer, QSize, QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager, QNetworkReply
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QComboBox, QWidget, QCheckBox, QRadioButton, \
    QButtonGroup, QFileDialog, QProgressBar, QLabel, QMessageBox, QDialogButtonBox, QGroupBox, QFormLayout, QStatusBar

import banner

from gui import HLayout, VLayout, GroupBoxH, GroupBoxV, SpinBox, dark_palette
from utils import MODULES, NoBinFile, NetworkError

BINS_URL = 'http://ota.tasmota.com'


class ESPWorker(QObject):
    error = pyqtSignal(Exception)
    waiting = pyqtSignal()
    done = pyqtSignal()

    def __init__(self, port, actions, **params):
        super().__init__()
        self.command = [
                      '--chip', 'esp8266',
                      '--port', port,
                      '--baud', '115200'
            ]

        self._actions = actions
        self._params = params
        self._continue = False

    @pyqtSlot()
    def run(self):
        esptool.sw.setContinueFlag(True)

        try:
            if 'backup' in self._actions:
                command_backup = ['read_flash', '0x00000', self._params['backup_size'],
                                  'backup_{}.bin'.format(datetime.now().strftime('%Y%m%d_%H%M%S'))]
                esptool.main(self.command + command_backup)

                auto_reset = self._params['auto_reset']
                if not auto_reset:
                    self.wait_for_user()

            if esptool.sw.continueFlag() and 'write' in self._actions:
                file_path = self._params['file_path']
                command_write = ['write_flash', '--flash_mode', 'dout', '0x00000', file_path]

                if 'erase' in self._actions:
                    command_write.append('--erase-all')
                esptool.main(self.command + command_write)

        except (esptool.FatalError, serial.SerialException) as e:
            self.error.emit(e)
        self.done.emit()

    def wait_for_user(self):
        self._continue = False
        self.waiting.emit()
        while not self._continue:
            sleep(.1)

    def continue_ok(self):
        self._continue = True

    def abort(self):
        esptool.sw.setContinueFlag(False)


class SendConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(640)
        self.setWindowTitle('Send configuration to device')
        self.settings = QSettings('tasmotizer.cfg', QSettings.IniFormat)

        self.commands = None
        self.module_mode = 0

        self.createUI()
        self.loadSettings()

    def createUI(self):
        vl = VLayout()
        self.setLayout(vl)

        # Wifi groupbox
        self.gbWifi = QGroupBox('WiFi')
        self.gbWifi.setCheckable(True)
        self.gbWifi.setChecked(False)
        flWifi = QFormLayout()
        self.leAP = QLineEdit()
        self.leAPPwd = QLineEdit()
        self.leAPPwd.setEchoMode(QLineEdit.Password)
        flWifi.addRow('SSID', self.leAP)
        flWifi.addRow('Password', self.leAPPwd)
        self.gbWifi.setLayout(flWifi)

        # Recovery Wifi groupbox
        self.gbRecWifi = QGroupBox('Recovery WiFi')
        self.gbRecWifi.setCheckable(True)
        self.gbRecWifi.setChecked(False)
        flRecWifi = QFormLayout()
        lbRecAP = QLabel('Recovery')
        lbRecAP.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        lbRecAPPwd = QLabel('a1b2c3d4')
        lbRecAPPwd.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        flRecWifi.addRow('SSID', lbRecAP)
        flRecWifi.addRow('Password', lbRecAPPwd)
        self.gbRecWifi.setLayout(flRecWifi)

        vl_wifis = VLayout(0)
        vl_wifis.addWidgets([self.gbWifi, self.gbRecWifi])

        # MQTT groupbox
        self.gbMQTT = QGroupBox('MQTT')
        self.gbMQTT.setCheckable(True)
        self.gbMQTT.setChecked(False)
        flMQTT = QFormLayout()
        self.leBroker = QLineEdit()
        self.sbPort = SpinBox()
        self.sbPort.setValue(1883)
        self.leTopic = QLineEdit()
        self.leTopic.setText('tasmota')
        self.leFullTopic = QLineEdit()
        self.leFullTopic.setText('%prefix%/%topic%/')
        self.leFriendlyName = QLineEdit()
        self.leMQTTUser = QLineEdit()
        self.leMQTTPass = QLineEdit()
        self.leMQTTPass.setEchoMode(QLineEdit.Password)

        flMQTT.addRow('Host', self.leBroker)
        flMQTT.addRow('Port', self.sbPort)
        flMQTT.addRow('Topic', self.leTopic)
        flMQTT.addRow('FullTopic', self.leFullTopic)
        flMQTT.addRow('FriendlyName', self.leFriendlyName)
        flMQTT.addRow('User [optional]', self.leMQTTUser)
        flMQTT.addRow('Password [optional]', self.leMQTTPass)
        self.gbMQTT.setLayout(flMQTT)

        # Module/template groupbox
        self.gbModule = GroupBoxV('Module/template')
        self.gbModule.setCheckable(True)
        self.gbModule.setChecked(False)

        hl_m_rb = HLayout()
        self.rbModule = QRadioButton('Module')
        self.rbModule.setChecked(True)
        self.rbTemplate = QRadioButton('Template')
        hl_m_rb.addWidgets([self.rbModule, self.rbTemplate])

        self.rbgModule = QButtonGroup(self.gbModule)
        self.rbgModule.addButton(self.rbModule, 0)
        self.rbgModule.addButton(self.rbTemplate, 1)

        self.cbModule = QComboBox()
        for mod_id, mod_name in MODULES.items():
            self.cbModule.addItem(mod_name, mod_id)

        self.leTemplate = QLineEdit()
        self.leTemplate.setPlaceholderText('Paste template string here')
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
        self.gbWifi.setChecked(self.settings.value('gbWifi', False, bool))
        self.leAP.setText(self.settings.value('AP'))

        self.gbRecWifi.setChecked(self.settings.value('gbRecWifi', False, bool))

        self.gbMQTT.setChecked(self.settings.value('gbMQTT', False, bool))
        self.leBroker.setText(self.settings.value('Broker'))
        self.sbPort.setValue(self.settings.value('Port', 1883, int))
        self.leTopic.setText(self.settings.value('Topic', 'tasmota'))
        self.leFullTopic.setText(self.settings.value('FullTopic', '%prefix%/%topic%/'))
        self.leFriendlyName.setText(self.settings.value('FriendlyName'))
        self.leMQTTUser.setText(self.settings.value('MQTTUser'))

        self.gbModule.setChecked(self.settings.value('gbModule', False, bool))

        module_mode = self.settings.value('ModuleMode', 0, int)
        for b in self.rbgModule.buttons():
            if self.rbgModule.id(b) == module_mode:
                b.setChecked(True)
                self.setModuleMode(module_mode)
        self.cbModule.setCurrentText(self.settings.value('Module', 'Generic'))
        self.leTemplate.setText(self.settings.value('Template'))

    def setModuleMode(self, radio):
        self.module_mode = radio
        self.cbModule.setVisible(not radio)
        self.leTemplate.setVisible(radio)

    def accept(self):
        ok = True

        if self.gbWifi.isChecked() and (len(self.leAP.text()) == 0 or len(self.leAPPwd.text()) == 0):
            ok = False
            QMessageBox.warning(self, 'WiFi details incomplete', 'Input WiFi AP and Password')

        if self.gbMQTT.isChecked() and not self.leBroker.text():
            ok = False
            QMessageBox.warning(self, 'MQTT details incomplete', 'Input broker hostname')

        if self.module_mode == 1 and len(self.leTemplate.text()) == 0:
            ok = False
            QMessageBox.warning(self, 'Template string missing', 'Input template string')

        if ok:
            backlog = []

            if self.gbWifi.isChecked():
                backlog.extend(['ssid1 {}'.format(self.leAP.text()), 'password1 {}'.format(self.leAPPwd.text())])

            if self.gbRecWifi.isChecked():
                backlog.extend(['ssid2 Recovery', 'password2 a1b2c3d4'])

            if self.gbMQTT.isChecked():
                backlog.extend(['mqtthost {}'.format(self.leBroker.text()), 'mqttport {}'.format(self.sbPort.value())])

                topic = self.leTopic.text()
                if topic and topic != 'tasmota':
                    backlog.append('topic {}'.format(topic))

                fulltopic = self.leFullTopic.text()
                if fulltopic and fulltopic != '%prefix%/%topic%/':
                    backlog.append('fulltopic {}'.format(fulltopic))

                fname = self.leFriendlyName.text()
                if fname:
                    backlog.append('friendlyname {}'.format(fname))

                mqttuser = self.leMQTTUser.text()
                if mqttuser:
                    backlog.append('mqttuser {}'.format(mqttuser))

                    mqttpassword = self.leMQTTPass.text()
                    if mqttpassword:
                        backlog.append('mqttpassword {}'.format(mqttpassword))

            if self.gbModule.isChecked():
                if self.module_mode == 0:
                    backlog.append('module {}'.format(self.cbModule.currentData()))

                elif self.module_mode == 1:
                    backlog.extend(['template {}'.format(self.leTemplate.text()), 'module 0'])

            self.commands = 'backlog {}\n'.format(';'.join(backlog))

            self.done(QDialog.Accepted)


class ProcessDialog(QDialog):
    def __init__(self, port, **kwargs):
        super().__init__()

        self.setWindowTitle('Tasmotizing...')
        self.setFixedWidth(400)

        self.exception = None

        esptool.sw.progress.connect(self.update_progress)

        self.nam = QNetworkAccessManager()
        self.nrBinFile = QNetworkRequest()
        self.bin_data = b''

        self.setLayout(VLayout(5, 5))
        self.actions_layout = QFormLayout()
        self.actions_layout.setSpacing(5)

        self.layout().addLayout(self.actions_layout)

        self._actions = []
        self._action_widgets = {}

        self.port = port

        self.auto_reset = kwargs.get('auto_reset', False)

        self.file_path = kwargs.get('file_path')
        if self.file_path and self.file_path.startswith('http'):
            self._actions.append('download')

        self.backup = kwargs.get('backup')
        if self.backup:
            self._actions.append('backup')
            self.backup_size = kwargs.get('backup_size')

        self.erase = kwargs.get('erase')
        if self.erase:
            self._actions.append('erase')

        if self.file_path:
            self._actions.append('write')

        self.create_ui()
        self.start_process()

    def create_ui(self):
        for action in self._actions:
            pb = QProgressBar()
            pb.setFixedHeight(35)
            self._action_widgets[action] = pb
            self.actions_layout.addRow(action.capitalize(), pb)

        self.btns = QDialogButtonBox(QDialogButtonBox.Abort)
        self.btns.rejected.connect(self.abort)
        self.layout().addWidget(self.btns)

        self.sb = QStatusBar()
        self.layout().addWidget(self.sb)

    def appendBinFile(self):
        self.bin_data += self.bin_reply.readAll()

    def saveBinFile(self):
        if self.bin_reply.error() == QNetworkReply.NoError:
            self.file_path = self.file_path.split('/')[-1]
            with open(self.file_path, 'wb') as f:
                f.write(self.bin_data)
            self.run_esp()
        else:
            raise NetworkError

    def updateBinProgress(self, recv, total):
        self._action_widgets['download'].setValue(recv//total*100)

    def download_bin(self):
        self.nrBinFile.setUrl(QUrl(self.file_path))
        self.bin_reply = self.nam.get(self.nrBinFile)
        self.bin_reply.readyRead.connect(self.appendBinFile)
        self.bin_reply.downloadProgress.connect(self.updateBinProgress)
        self.bin_reply.finished.connect(self.saveBinFile)

    def show_connection_state(self, state):
        self.sb.showMessage(state, 0)

    def run_esp(self):
        params = {
            'file_path': self.file_path,
            'auto_reset': self.auto_reset,
            'erase': self.erase
        }

        if self.backup:
            backup_size = f'0x{2 ** self.backup_size}00000'
            params['backup_size'] = backup_size

        self.esp_thread = QThread()
        self.esp = ESPWorker(
            self.port,
            self._actions,
            **params
        )
        esptool.sw.connection_state.connect(self.show_connection_state)
        self.esp.waiting.connect(self.wait_for_user)
        self.esp.done.connect(self.accept)
        self.esp.error.connect(self.error)
        self.esp.moveToThread(self.esp_thread)
        self.esp_thread.started.connect(self.esp.run)
        self.esp_thread.start()

    def start_process(self):
        if 'download' in self._actions:
            self.download_bin()
            self._actions = self._actions[1:]
        else:
            self.run_esp()

    def update_progress(self, action, value):
        self._action_widgets[action].setValue(value)

    @pyqtSlot()
    def wait_for_user(self):
        dlg = QMessageBox.information(self,
                                      'User action required',
                                      'Please power cycle the device, wait a moment and press OK',
                                      QMessageBox.Ok | QMessageBox.Cancel)
        if dlg == QMessageBox.Ok:
            self.esp.continue_ok()
        elif dlg == QMessageBox.Cancel:
            self.esp.abort()
            self.esp.continue_ok()
            self.abort()

    def stop_thread(self):
        self.esp_thread.wait(2000)
        self.esp_thread.exit()

    def accept(self):
        self.stop_thread()
        self.done(QDialog.Accepted)

    def abort(self):
        self.sb.showMessage('Aborting...', 0)
        QApplication.processEvents()
        self.esp.abort()
        self.stop_thread()
        self.reject()

    def error(self, e):
        self.exception = e
        self.abort()

    def closeEvent(self, e):
        self.stop_thread()


class DeviceIP(QDialog):
    def __init__(self, port: QSerialPort):
        super(DeviceIP, self).__init__()

        self.setWindowTitle('Device IP address')
        self.setLayout(VLayout(10))

        self.ip = QLineEdit()
        self.ip.setAlignment(Qt.AlignCenter)
        self.ip.setReadOnly(True)
        self.ip.setText('xx.xx.xx.xx')
        font = self.ip.font()
        font.setPointSize(24)
        self.ip.setFont(font)

        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(self.reject)

        self.layout().addWidgets([self.ip, btn])

        self.data = b''

        self.port = port

        self.re_ip = re.compile(r'(?:\()((?:[0-9]{1,3}\.){3}[0-9]{1,3})(?:\))')

        try:
            self.port.open(QIODevice.ReadWrite)
            self.port.readyRead.connect(self.read)
            self.port.write(bytes('IPAddress1\n', 'utf8'))
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Port access error:\n{e}')

    def read(self):
        try:
            self.data += self.port.readAll()
            match = self.re_ip.search(bytes(self.data).decode('utf8'))
            if match:
                self.ip.setText(match[1])
        except:
            pass


class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()
        self.settings = QSettings('tasmotizer.cfg', QSettings.IniFormat)

        self.port = ''

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl(f'{BINS_URL}/tasmota/release/release.php'))
        self.nrDevelopment = QNetworkRequest(QUrl(f'{BINS_URL}/tasmota/development.php'))

        self.esp_thread = None

        self.setWindowTitle('Tasmotizer 1.2')
        self.setMinimumWidth(480)

        self.mode = 0  # BIN file
        self.file_path = ''

        self.release_data = b''
        self.development_data = b''

        self.create_ui()

        self.refreshPorts()
        self.getFeeds()

    def create_ui(self):
        vl = VLayout(5)
        self.setLayout(vl)

        # Banner
        banner = QLabel()
        banner.setPixmap(QPixmap(':/banner.png'))
        vl.addWidget(banner)

        # Port groupbox
        gbPort = GroupBoxH('Select port', 3)
        self.cbxPort = QComboBox()
        pbRefreshPorts = QPushButton('Refresh')
        gbPort.addWidget(self.cbxPort)
        gbPort.addWidget(pbRefreshPorts)
        gbPort.layout().setStretch(0, 4)
        gbPort.layout().setStretch(1, 1)

        # Firmware groupbox
        gbFW = GroupBoxV('Select image', 3)

        hl_rb = HLayout(0)
        rbFile = QRadioButton('BIN file')
        self.rbRelease = QRadioButton('Release')
        self.rbRelease.setEnabled(False)
        self.rbDev = QRadioButton('Development')
        self.rbDev.setEnabled(False)

        self.rbgFW = QButtonGroup(gbFW)
        self.rbgFW.addButton(rbFile, 0)
        self.rbgFW.addButton(self.rbRelease, 1)
        self.rbgFW.addButton(self.rbDev, 2)

        hl_rb.addWidgets([rbFile, self.rbRelease, self.rbDev])
        gbFW.addLayout(hl_rb)

        self.wFile = QWidget()
        hl_file = HLayout(0)
        self.file = QLineEdit()
        self.file.setReadOnly(True)
        self.file.setPlaceholderText('Click "Open" to select the image')
        pbFile = QPushButton('Open')
        hl_file.addWidgets([self.file, pbFile])
        self.wFile.setLayout(hl_file)

        self.cbHackboxBin = QComboBox()
        self.cbHackboxBin.setVisible(False)
        self.cbHackboxBin.setEnabled(False)

        self.cbSelfReset = QCheckBox('Self-resetting device (NodeMCU, Wemos)')
        self.cbSelfReset.setToolTip('Check if your device has self-resetting capabilities supported by esptool')

        gbBackup = GroupBoxV('Backup')
        self.cbBackup = QCheckBox('Save original firmware')
        self.cbBackup.setToolTip('Firmware backup is ESPECIALLY recommended when you flash a Sonoff, Tuya, Shelly etc. for the first time.\nWithout a backup you will not be able to restore the original functionality.')

        self.cbxBackupSize = QComboBox()
        self.cbxBackupSize.addItems([f'{2 ** s}MB' for s in range(5)])
        self.cbxBackupSize.setEnabled(False)

        hl_backup_size = HLayout(0)
        hl_backup_size.addWidgets([QLabel('Flash size:'), self.cbxBackupSize])
        hl_backup_size.setStretch(0, 3)
        hl_backup_size.setStretch(1, 1)

        gbBackup.addWidget(self.cbBackup)
        gbBackup.addLayout(hl_backup_size)

        self.cbErase = QCheckBox('Erase before flashing')
        self.cbErase.setToolTip('Erasing previous firmware ensures all flash regions are clean for Tasmota, which prevents many unexpected issues.\nIf unsure, leave enabled.')
        self.cbErase.setChecked(True)

        gbFW.addWidgets([self.wFile, self.cbHackboxBin, self.cbSelfReset, self.cbErase])

        # Buttons
        self.pbTasmotize = QPushButton('Tasmotize!')
        self.pbTasmotize.setFixedHeight(50)
        self.pbTasmotize.setStyleSheet('background-color: #223579;')

        self.pbConfig = QPushButton('Send config')
        self.pbConfig.setStyleSheet('background-color: #571054;')
        self.pbConfig.setFixedHeight(50)

        self.pbGetIP = QPushButton('Get IP')
        self.pbGetIP.setFixedSize(QSize(75, 50))
        self.pbGetIP.setStyleSheet('background-color: #2a8a26;')

        self.pbQuit = QPushButton('Quit')
        self.pbQuit.setStyleSheet('background-color: #c91017;')
        self.pbQuit.setFixedSize(QSize(50, 50))

        hl_btns = HLayout([50, 3, 50, 3])
        hl_btns.addWidgets([self.pbTasmotize, self.pbConfig, self.pbGetIP, self.pbQuit])

        vl.addWidgets([gbPort, gbBackup, gbFW])
        vl.addLayout(hl_btns)

        pbRefreshPorts.clicked.connect(self.refreshPorts)
        self.rbgFW.buttonClicked[int].connect(self.setBinMode)
        rbFile.setChecked(True)
        pbFile.clicked.connect(self.openBinFile)

        self.cbBackup.toggled.connect(self.cbxBackupSize.setEnabled)

        self.pbTasmotize.clicked.connect(self.start_process)
        self.pbConfig.clicked.connect(self.send_config)
        self.pbGetIP.clicked.connect(self.get_ip)
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

    def getFeeds(self):
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
        self.fill_bin_combo(self.release_data, self.rbRelease)

    def processDevelopmentInfo(self):
        self.fill_bin_combo(self.development_data, self.rbDev)

    def fill_bin_combo(self, data, rb):
        try:
            reply = json.loads(str(data, 'utf8'))
            version, bins = list(reply.items())[0]
            version = version.replace('-', ' ').title()

            rb.setText(version)
            if len(bins) > 0:
                self.cbHackboxBin.clear()
                for img in bins:
                    img['filesize'] //= 1024
                    self.cbHackboxBin.addItem('{binary} [{filesize}kB]'.format(**img), '{otaurl}'.format(**img))
                self.cbHackboxBin.setEnabled(True)
        except json.JSONDecodeError as e:
            self.setBinMode(0)
            self.rbgFW.button(0).setChecked(True)
            QMessageBox.critical(self, 'Error', f'Cannot load bin data:\n{e.msg}')

    def openBinFile(self):
        previous_file = self.settings.value('bin_file')
        file, ok = QFileDialog.getOpenFileName(self, 'Select Tasmota image', previous_file, filter='BIN files (*.bin)')
        if ok:
            self.file.setText(file)

    def get_ip(self):
        self.port = QSerialPort(self.cbxPort.currentData())
        self.port.setBaudRate(115200)

        DeviceIP(self.port).exec_()

        if self.port.isOpen():
            self.port.close()

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
                    QMessageBox.critical(self, 'Error', f'Port access error:\n{e}')
                else:
                    self.settings.setValue('gbWifi', dlg.gbWifi.isChecked())
                    self.settings.setValue('AP', dlg.leAP.text())

                    self.settings.setValue('gbRecWifi', dlg.gbRecWifi.isChecked())

                    self.settings.setValue('gbMQTT', dlg.gbMQTT.isChecked())
                    self.settings.setValue('Broker', dlg.leBroker.text())
                    self.settings.setValue('Port', dlg.sbPort.value())
                    self.settings.setValue('Topic', dlg.leTopic.text())
                    self.settings.setValue('FullTopic', dlg.leFullTopic.text())
                    self.settings.setValue('FriendlyName', dlg.leFriendlyName.text())
                    self.settings.setValue('MQTTUser', dlg.leMQTTUser.text())

                    self.settings.setValue('gbModule', dlg.gbModule.isChecked())
                    self.settings.setValue('ModuleMode', dlg.rbgModule.checkedId())
                    self.settings.setValue('Module', dlg.cbModule.currentText())
                    self.settings.setValue('Template', dlg.leTemplate.text())
                    self.settings.sync()

                    QMessageBox.information(self, 'Done', 'Configuration sent ({} bytes)\nDevice will restart.'.format(bytes_sent))
                finally:
                    if self.port.isOpen():
                        self.port.close()
            else:
                QMessageBox.information(self, 'Done', 'Nothing to send')

    def start_process(self):
        try:
            if self.mode == 0:
                if len(self.file.text()) > 0:
                    self.file_path = self.file.text()
                    self.settings.setValue('bin_file', self.file_path)
                else:
                    raise NoBinFile

            elif self.mode in (1, 2):
                self.file_path = self.cbHackboxBin.currentData()

            process_dlg = ProcessDialog(
                self.cbxPort.currentData(),
                file_path=self.file_path,
                backup=self.cbBackup.isChecked(),
                backup_size=self.cbxBackupSize.currentIndex(),
                erase=self.cbErase.isChecked(),
                auto_reset=self.cbSelfReset.isChecked()
            )
            result = process_dlg.exec_()
            if result == QDialog.Accepted:
                message = 'Process successful!'
                if not self.cbSelfReset.isChecked():
                    message += ' Power cycle the device.'

                QMessageBox.information(self, 'Done', message)
            elif result == QDialog.Rejected:
                if process_dlg.exception:
                    QMessageBox.critical(self, 'Error', str(process_dlg.exception))
                else:
                    QMessageBox.critical(self, 'Process aborted', 'The process has been aborted by the user.')
            
        except NoBinFile:
            QMessageBox.critical(self, 'Image path missing', 'Select a binary to write, or select a different mode.')
        except NetworkError as e:
            QMessageBox.critical(self, 'Network error', e.message)


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
    app.setQuitOnLastWindowClosed(True)
    app.setStyle('Fusion')

    app.setPalette(dark_palette)
    app.setStyleSheet('QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }')
    app.setStyle('Fusion')

    mw = Tasmotizer()
    mw.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
