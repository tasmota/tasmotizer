from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QGroupBox, QSpinBox, QHBoxLayout, QDialog, QProgressBar, \
    QPushButton, QButtonGroup, QDialogButtonBox, QLabel


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


# class Config(QDialog):
#     def __init__(self):
#         super().self()
#
#         # Wifi groupbox
#         self.gbWifi = QGroupBox("WiFi")
#         self.gbWifi.setCheckable(True)
#         self.gbWifi.setChecked(False)
#         flWifi = QFormLayout()
#         self.leAP = QLineEdit()
#         self.leAPPwd = QLineEdit()
#         flWifi.addRow("SSID", self.leAP)
#         flWifi.addRow("Password", self.leAPPwd)
#         self.gbWifi.setLayout(flWifi)
#         self.gbWifi.setVisible(False)
#
#         # Recovery Wifi groupbox
#         self.gbRecWifi = QGroupBox("Recovery WiFi")
#         self.gbRecWifi.setCheckable(True)
#         self.gbRecWifi.setChecked(False)
#         flRecWifi = QFormLayout()
#         lbRecAP = QLabel("Recovery")
#         lbRecAP.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
#         lbRecAPPwd = QLabel("a1b2c3d4")
#         lbRecAPPwd.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
#
#         flRecWifi.addRow("SSID", lbRecAP)
#         flRecWifi.addRow("Password", lbRecAPPwd)
#         self.gbRecWifi.setLayout(flRecWifi)
#         self.gbRecWifi.setVisible(False)
#
#         # MQTT groupbox
#         self.gbMQTT = QGroupBox("MQTT")
#         self.gbMQTT.setCheckable(True)
#         self.gbMQTT.setChecked(False)
#         flMQTT = QFormLayout()
#         self.leBroker = QLineEdit()
#         self.sbPort = SpinBox()
#         self.sbPort.setValue(1883)
#         self.leTopic = QLineEdit()
#         self.leMQTTUser = QLineEdit()
#         self.leMQTTPass = QLineEdit()
#         flMQTT.addRow("Host", self.leBroker)
#         flMQTT.addRow("Port", self.sbPort)
#         flMQTT.addRow("Topic", self.leTopic)
#         flMQTT.addRow("User [optional]", self.leMQTTUser)
#         flMQTT.addRow("Password [optional]", self.leMQTTPass)
#         self.gbMQTT.setLayout(flMQTT)
#         self.gbMQTT.setVisible(False)
#
#         # Module/template groupbox
#         self.gbModule = GroupBoxV("Module/template")
#         self.gbModule.setCheckable(True)
#         self.gbModule.setChecked(False)
#
#         hl_m_rb = HLayout()
#         self.rbModule = QRadioButton("Module")
#         self.rbModule.setChecked(True)
#         self.rbTemplate = QRadioButton("Template")
#         hl_m_rb.addWidgets([self.rbModule, self.rbTemplate])
#
#         rbgModule = QButtonGroup(gbFW)
#         rbgModule.addButton(self.rbModule, 0)
#         rbgModule.addButton(self.rbTemplate, 1)
#
#         self.cbModule = QComboBox()
#         for mod_id, mod_name in modules.items():
#             self.cbModule.addItem(mod_name, mod_id)
#
#         self.leTemplate = QLineEdit()
#         self.leTemplate.setVisible(False)
#
#         self.gbModule.addLayout(hl_m_rb)
#         self.gbModule.addWidgets([self.cbModule, self.leTemplate])
#         self.gbModule.setVisible(False)
#
#         # add all widgets to main layout
#         #         vl_main_left.addWidgets([gbPort, gbFW, self.gbWifi, self.gbRecWifi, self.gbMQTT, self.gbModule])
#         vl_main_left.addWidgets([gbPort, gbFW, self.gbWifi, self.gbRecWifi])
#         #         vl_main_left.addWidgets([gbPort, gbFW])
#         vl_main_right.addWidgets([self.gbMQTT, self.gbModule])

    # def setModuleMode(self, radio):
    #     self.module_mode = radio
    #     self.cbModule.setVisible(not radio)
    #     self.leTemplate.setVisible(radio)

    # rbgModule.buttonClicked[int].connect(self.setModuleMode)