import json

from PyQt5.QtCore import QSettings, QUrl, QSize, QIODevice
from PyQt5.QtGui import QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtSerialPort import QSerialPortInfo, QSerialPort
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QRadioButton, QButtonGroup, QWidget, QLineEdit, \
    QCheckBox, QMessageBox, QFileDialog

from gui.device_ip import DeviceIP
from gui.process import ProcessDialog
from gui.send_config import SendConfigDialog
from gui.widgets import VLayout, GroupBoxH, GroupBoxV, HLayout
from utils import BINS_URL, NoBinFile, NetworkError


__version__ = '1.3a0'

class Tasmotizer(QDialog):

    def __init__(self):
        super().__init__()
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'tasmota', 'tasmotizer')

        self.port = ''

        self.nam = QNetworkAccessManager()
        self.nrRelease = QNetworkRequest(QUrl(f'{BINS_URL}/tasmota/release/release.php'))
        self.nrDevelopment = QNetworkRequest(QUrl(f'{BINS_URL}/tasmota/development.php'))

        self.esp_thread = None

        self.setWindowTitle(f'Tasmotizer {__version__}')
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
                    commands = f'backlog {";".join(dlg.commands)}\n'
                    bytes_sent = self.port.write(bytes(commands, 'utf8'))
                    QMessageBox.information(self, 'Done',
                                            'Configuration sent ({} bytes)\nDevice will restart.'.format(bytes_sent))
                except Exception as e:
                    QMessageBox.critical(self, 'Error', f'Port access error:\n{e}')
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