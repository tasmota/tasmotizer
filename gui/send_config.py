import os
import keyring

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QWidget, QFormLayout, QLineEdit, QLabel, QListWidget, \
    QStackedWidget, QListWidgetItem, QMessageBox, QCheckBox

from gui.widgets import VLayout, HLayout, SpinBox, Password, Modules, TemplateComboBox
from utils import MissingDetail


class Setting:
    def __init__(self, command, description, widget_class, required=False, **kwargs):
        self.command = command
        self.description = description
        self._widget_class = widget_class
        self._widget = None
        self.required = required

        self.default = kwargs.get('default', None)
        self.align = kwargs.get('align', None)

        self._settings = None

    def apply_settings(self, settings):
        self._settings = settings

    def widget(self):
        self._widget = self._widget_class()
        try:
            if isinstance(self._widget, Password):
                value = keyring.get_password('tasmotizer', self.command)
            else:
                value = self._settings.value(self.command, self.default)
        except keyring.errors.KeyringError:
            QMessageBox.critical(self, "Error", "Tasmotizer is unable to use your system keyring")

        if value:
            if isinstance(self._widget, SpinBox):
                self._widget.setValue(int(value))

            elif isinstance(self._widget, QCheckBox):
                self._widget.setChecked(True if value == '1' else False)

            elif isinstance(self._widget, TemplateComboBox):
                user_templates_file = os.path.sep.join([os.path.dirname(self._settings.fileName()), 'templates.txt'])
                if os.path.exists(user_templates_file):
                    with open(user_templates_file, 'r') as user_tpl:
                        for entry in user_tpl.readlines():
                            if len(entry) > 1:
                                entry = entry.rstrip('\n')
                                self._widget.addItem(entry)
                self._widget.setCurrentText(value)

            elif isinstance(self._widget, Modules):
                self._widget.setCurrentIndex(int(value))

            else:
                self._widget.setText(value)

        if self.align:
            self._widget.setAlignment(self.align)

        return self._widget

    def serial_command(self):
        if isinstance(self._widget, SpinBox):
            value = self._widget.value()
        elif isinstance(self._widget, Modules):
            value = self._widget.currentData()
        elif isinstance(self._widget, QCheckBox):
            value = 1 if self._widget.isChecked() else 0
        elif isinstance(self._widget, TemplateComboBox):
            value = self._widget.currentText().rstrip('\n')
        else:
            value = self._widget.text()

        if self.required and not value:
            raise MissingDetail(f'{self.section} setting missing', f"{self._settings['desc']} is required.")

        if value != self.default or isinstance(self._widget, QLabel):
            try:
                if isinstance(self._widget, Password):
                    keyring.set_password('tasmotizer', self.command, value)
                else:
                    self._settings.setValue(self.command, value)
            except keyring.errors.KeyringError:
                QMessageBox.critical(self, "Error", "Tasmotizer is unable to use your system keyring")

            return f'{self.command} {value}'


configs = {
    'Hostname':
        [
            Setting(command='hostname', description='Hostname', widget_class=QLineEdit, required=True),
        ],
    'WiFi':
        [
            Setting(command='ssid1', description='AP1', widget_class=QLineEdit, required=True),
            Setting(command='password1', description='Password1', widget_class=Password, required=True),
        ],
    'Recovery WiFi':
        [
            Setting(command='ssid2', description='AP2', widget_class=QLabel, default='Tasmota Recovery', align=Qt.AlignVCenter | Qt.AlignRight),
            Setting(command='password2', description='Password1', widget_class=QLabel, default='a1b2c3d4', align=Qt.AlignVCenter | Qt.AlignRight),
        ],
    'Static IP':
        [
            Setting(command='ipaddress1', description='IP', widget_class=QLineEdit, required=True),
            Setting(command='ipaddress2', description='Gateway', widget_class=QLineEdit, required=True),
            Setting(command='ipaddress3', description='Subnet', widget_class=QLineEdit, required=True, default='255.255.255.0'),
            Setting(command='ipaddress4', description='DNS Server', widget_class=QLineEdit),
        ],
    'MQTT':
        [
            Setting(command='mqtthost', description='Broker', widget_class=QLineEdit, required=True),
            Setting(command='mqttport', description='Port', widget_class=SpinBox, default=1883),
            Setting(command='topic', description='Topic', widget_class=QLineEdit, required=True, default='tasmota_%06X'),
            Setting(command='fulltopic', description='FullTopic', widget_class=QLineEdit, required=True, default='%prefix%/%topic%/'),
        ],
    'MQTT Auth':
        [
            Setting(command='mqttuser', description='User', widget_class=QLineEdit, required=True),
            Setting(command='mqttpassword', description='Password', widget_class=Password),
        ],
    'Module':
        [
            Setting(command='module', description='Module', widget_class=Modules),
        ],
    'Template':
        [
            Setting(command='template', description='Template', widget_class=TemplateComboBox, required=True),
        ],
    'CORS':
        [
            Setting(command='cors', description='CORS Domain', widget_class=QLineEdit, required=True, default='*'),
        ],
    'SetOptions':
        [
            Setting(command='setoption19', description='Enable HomeAssistant auto-discovery (SetOption19)', widget_class=QCheckBox),
            Setting(command='setoption52', description='Display optional time offset from UTC in JSON payloads (SetOption52)', widget_class=QCheckBox),
            Setting(command='setoption65', description='Tasmota won\'t erase the settings after 4 quick power cycles (SetOption65)', widget_class=QCheckBox),
        ]
}


class ConfigWidget(QWidget):
    def __init__(self, section, content):
        super(ConfigWidget, self).__init__()
        self.setLayout(QFormLayout())
        self.section = section
        self.content = content

        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'tasmota', 'tasmotizer')

        for setting in self.content:
            setting.apply_settings(self.settings)
            self.layout().addRow(setting.description, setting.widget())

    def collect_and_save(self):
        return [setting.serial_command() for setting in self.content]


class SendConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Send configuration to device')
        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'tasmota', 'tasmotizer')

        self.commands = []
        self.module_mode = 0

        vl = VLayout()
        self.setLayout(vl)

        hl = HLayout(0)
        self.config_list = QListWidget()
        self.config_list.setMinimumWidth(150)
        self.config_list.setAlternatingRowColors(True)
        self.config_stack = QStackedWidget()
        self.config_stack.setMaximumWidth(500)

        for section, content in configs.items():
            widget = ConfigWidget(section, content)
            self.config_stack.addWidget(widget)
            config_list_item = QListWidgetItem(section)
            config_list_item.setFlags(config_list_item.flags() | Qt.ItemIsUserCheckable)
            config_list_item.setCheckState(self.settings.value(section, Qt.Unchecked, int))
            self.config_list.addItem(config_list_item)
        hl.addWidgets([self.config_list, self.config_stack])
        hl.setStretch(0, 2)
        hl.setStretch(1, 1)

        vl.addLayout(hl)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Close)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        vl.addWidget(btns)

        self.config_list.currentRowChanged.connect(self.config_stack.setCurrentIndex)
        self.config_list.doubleClicked.connect(self.toggle_item_check)

    def toggle_item_check(self, idx):
        item = self.config_list.item(idx.row())
        if item.checkState() == Qt.Unchecked:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def accept(self):
        try:
            for row in range(self.config_list.count()):
                item = self.config_list.item(row)
                widget = self.config_stack.widget(row)
                if item.checkState() == Qt.Checked:
                    self.commands.extend(widget.collect_and_save())
                    self.settings.setValue(widget.section, Qt.Checked)
                else:
                    self.settings.remove(widget.section)
            if self.commands:
                self.commands.append("restart 1")
                self.done(QDialog.Accepted)
            else:
                QMessageBox.warning(self, "Warning", "Nothing to send.\nTick one of the checkboxes on the list.")

        except MissingDetail as e:
            QMessageBox.critical(self, e.args[0], e.args[1])
