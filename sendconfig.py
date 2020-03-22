import os

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QWidget, QFormLayout, QLineEdit, QLabel, QListWidget, \
    QStackedWidget, QListWidgetItem, QMessageBox, QCheckBox

from gui import VLayout, HLayout, SpinBox, Password, Modules, TemplateComboBox

configs = {
    'Hostname':
        {
            'hostname': {
                'desc': 'Hostname',
                'widget': QLineEdit,
                'required': True,
            },
        },
    'WiFi':
        {
            'ssid1': {
                'desc': 'AP1',
                'widget': QLineEdit,
                'required': True,
            },
            'password1': {
                'desc': 'Password1',
                'widget': Password,
                'required': True,
                'keep': False,
            },
        },
    'Recovery WiFi':
        {
            'ssid2': {
                'desc': 'AP2',
                'widget': QLabel,
                'default': 'Recovery',
                'keep': False,
                'align': Qt.AlignVCenter | Qt.AlignRight
            },
            'password2': {
                'desc': 'Password2',
                'widget': QLabel,
                'default': 'a1b2c3d4',
                'keep': False,
                'align': Qt.AlignVCenter | Qt.AlignRight
                }
        },
    'Static IP':
        {
            'ipaddress1': {
                'desc': 'IP',
                'widget': QLineEdit,
                'required': True,
            },
            'ipaddress2': {
                'desc': 'Gateway',
                'widget': QLineEdit,
                'required': True,
            },
            'ipaddress3': {
                'desc': 'Subnet',
                'widget': QLineEdit,
                'required': True,
                'default': '255.255.255.0'
            },
            'ipaddress4': {
                'desc': 'DNS Server',
                'widget': QLineEdit,
            },
        },
    'MQTT':
        {
            'mqtthost': {
                'desc': 'Broker',
                'widget': QLineEdit,
                'required': True,
            },
            'mqttport': {
                'desc': 'Port',
                'widget': SpinBox,
                'default': 1883,
            },
            'topic': {
                'desc': 'Topic',
                'widget': QLineEdit,
                'required': True,
                'default': 'tasmota_%06X',
            },
            'fulltopic': {
                'desc': 'Fulltopic',
                'widget': QLineEdit,
                'required': True,
                'default': '%prefix%/%topic%/',
            },
        },
    'MQTT Auth':
        {
            'mqttuser': {
                'desc': 'User',
                'widget': QLineEdit,
                'required': True,
            },
            'mqttpassword': {
                'desc': 'Password',
                'widget': Password,
                'required': True,
                'keep': False,
            },
        },
    'Module':
        {
            'module': {
                'desc': 'Module',
                'widget': Modules,
            },
        },
    'Template':
        {
            'template': {
                'desc': 'Template',
                'widget': TemplateComboBox,
                'required': True,
            },
        },
    'CORS':
        {
            'cors': {
                'desc': 'CORS domain',
                'widget': QLineEdit,
                'required': True,
                'default': '*'
            },
        },
    'SetOptions':
        {
            'setoption19': {
                'desc': 'Enable HomeAssistant auto-discovery (SetOption19)',
                'widget': QCheckBox,
            },
            'setoption52': {
                'desc': 'Display optional time offset from UTC in JSON payloads (SetOption52)',
                'widget': QCheckBox,
            },
            'setoption65': {
                'desc': 'Tasmota won\'t erase the settings after 4 quick power cycles (SetOption65)',
                'widget': QCheckBox,
            },
        }
}


class MissingDetailException(Exception):
    pass


class ConfigWidget(QWidget):
    def __init__(self, section, content):
        super(ConfigWidget, self).__init__()
        self.setLayout(QFormLayout())
        self.section = section
        self.content = content

        self.settings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'tasmota', 'tasmotizer')

        for command, settings in content.items():
            widget = settings['widget']()
            setattr(self, command, widget)

            value = self.settings.value(command, settings.get('default'))
            if value:
                if isinstance(widget, SpinBox):
                    widget.setValue(int(value))

                elif isinstance(widget, TemplateComboBox):
                    user_templates_file = os.path.sep.join([os.path.dirname(self.settings.fileName()), 'templates.txt'])
                    if os.path.exists(user_templates_file):
                        with open(user_templates_file, 'r') as user_tpl:
                            for entry in user_tpl.readlines():
                                if len(entry) > 1:
                                    entry = entry.rstrip('\n')
                                    widget.addItem(entry)
                    widget.setCurrentText(value)

                else:
                    widget.setText(value)

            align = settings.get('align')
            if align:
                widget.setAlignment(align)

            self.layout().addRow(settings['desc'], widget)

    def collect_and_save(self):
        commands = []
        for command, settings in self.content.items():
            widget = getattr(self, command)
            if isinstance(widget, SpinBox):
                value = widget.value()
            elif isinstance(widget, Modules):
                value = widget.currentData()
            elif isinstance(widget, QCheckBox):
                value = 1 if widget.isChecked() else 0
            elif isinstance(widget, TemplateComboBox):
                value = widget.currentText().rstrip('\n')
            else:
                value = widget.text()

            if settings.get('required') and not value:
                raise MissingDetailException(f'{self.section} setting missing', f"{settings['desc']} is required.")

            if value != settings.get('default') or isinstance(widget, QLabel):
                commands.append(f'{command} {value}')
                if settings.get('keep', True):
                    self.settings.setValue(command, value)

        return commands


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
                self.done(QDialog.Accepted)
            else:
                QMessageBox.warning(self, "Warning", "Nothing to send.\nTick one of the checkboxes on the list.")

        except MissingDetailException as e:
            QMessageBox.critical(self, e.args[0], e.args[1])
