import re

from PyQt5.QtCore import Qt, QIODevice
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QMessageBox

from gui.widgets import VLayout


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
            QMessageBox.critical(self, _('Error'), f_('Port access error:\n{e}'))

    def read(self):
        try:
            self.data += self.port.readAll()
            match = self.re_ip.search(bytes(self.data).decode('utf8'))
            if match:
                self.ip.setText(match[1])
        except:
            pass