from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QDialog, QGroupBox, QFormLayout, QLineEdit, QLabel, QRadioButton, QButtonGroup, QComboBox, \
    QDialogButtonBox, QMessageBox

from gui.widgets import VLayout, SpinBox, GroupBoxV, HLayout
from utils import MODULES


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