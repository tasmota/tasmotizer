from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QGroupBox, QSpinBox, QHBoxLayout, QTabWidget, QLineEdit, \
    QComboBox

modules = {'1': 'Sonoff Basic', '2': 'Sonoff RF', '4': 'Sonoff TH', '5': 'Sonoff Dual', '39': 'Sonoff Dual R2',
           '6': 'Sonoff Pow', '43': 'Sonoff Pow R2', '7': 'Sonoff 4CH', '23': 'Sonoff 4CH Pro', '41': 'Sonoff S31',
           '8': 'Sonoff S2X', '10': 'Sonoff Touch', '28': 'Sonoff T1 1CH', '29': 'Sonoff T1 2CH', '30': 'Sonoff T1 3CH',
           '11': 'Sonoff LED', '22': 'Sonoff BN-SZ', '70': 'Sonoff L1', '26': 'Sonoff B1', '9': 'Slampher',
           '21': 'Sonoff SC', '44': 'Sonoff iFan02', '71': 'Sonoff iFan03', '25': 'Sonoff Bridge', '3': 'Sonoff SV',
           '19': 'Sonoff Dev', '12': '1 Channel', '13': '4 Channel', '14': 'Motor C/AC', '15': 'ElectroDragon',
           '16': 'EXS Relay(s)', '31': 'Supla Espablo', '35': 'Luani HVIO', '33': 'Yunshan Relay', '17': 'WiOn',
           '46': 'Shelly 1', '47': 'Shelly 2', '45': 'BlitzWolf SHP', '52': 'Teckin', '59': 'Teckin US',
           '53': 'AplicWDP303075', '55': 'Gosund SP1 v23', '65': 'Luminea ZX2820', '57': 'SK03 Outdoor',
           '63': 'Digoo DG-SP202', '64': 'KA10', '67': 'SP10', '68': 'WAGA CHCZ02MB', '49': 'Neo Coolcam',
           '51': 'OBI Socket', '61': 'OBI Socket 2', '60': 'Manzoku strip', '50': 'ESP Switch', '54': 'Tuya MCU',
           '56': 'ARMTR Dimmer', '58': 'PS-16-DZ', '20': 'H801', '34': 'MagicHome', '37': 'Arilux LC01',
           '40': 'Arilux LC06', '38': 'Arilux LC11', '42': 'Zengge WF017', '24': 'Huafan SS', '36': 'KMC 70011',
           '27': 'AiLight', '48': 'Xiaomi Philips', '69': 'SYF05', '62': 'YTF IR Bridge', '32': 'Witty Cloud',
           '18': 'Generic'}


class LayoutMixin:
    def addWidgets(self, widgets):
        for w in widgets:
            self.addWidget(w)

    def addSpacer(self):
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.addWidget(spacer)


class GroupLayoutMixin:
    def addWidget(self, w):
        self.layout().addWidget(w)

    def addWidgets(self, widgets):
        for w in widgets:
            self.layout().addWidget(w)

    def addLayout(self, w):
        self.layout().addLayout(w)


class VLayout(QVBoxLayout, LayoutMixin):
    def __init__(self, margin=3, spacing=3):
        super().__init__()
        if isinstance(margin, int):
            self.setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list):
            self.setContentsMargins(margin[0], margin[1], margin[2], margin[3])

        self.setSpacing(spacing)


class HLayout(QHBoxLayout, LayoutMixin):
    def __init__(self, margin=3, spacing=3):
        super().__init__()
        if isinstance(margin, int):
            self.setContentsMargins(margin, margin, margin, margin)
        elif isinstance(margin, list):
            self.setContentsMargins(margin[0], margin[1], margin[2], margin[3])
        self.setSpacing(spacing)


class GroupBoxV(QGroupBox, GroupLayoutMixin):
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


class GroupBoxH(QGroupBox, GroupLayoutMixin):
    def __init__(self, title, margin=None, spacing=None, *args, **kwargs):
        super(GroupBoxH, self).__init__(title)
        self.setLayout(HLayout())


class SpinBox(QSpinBox):
    def __init__(self, *args, **kwargs):
        super(SpinBox, self).__init__(*args, **kwargs)
        self.setButtonSymbols(self.NoButtons)
        self.setMinimum(kwargs.get('minimum', 1))
        self.setMaximum(kwargs.get('maximum', 65535))


class Password(QLineEdit):
    def __init__(self):
        super(Password, self).__init__()
        self.setEchoMode(QLineEdit.Password)


class Modules(QComboBox):
    def __init__(self):
        super(Modules, self).__init__()
        for id, name in modules.items():
            self.addItem(name, id)


class TemplateComboBox(QComboBox):
    def __init__(self):
        super(TemplateComboBox, self).__init__()
        self.setEditable(True)


dark_palette = QPalette()
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.WindowText, Qt.white)
dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
dark_palette.setColor(QPalette.Base, QColor(15, 15, 15))
dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
dark_palette.setColor(QPalette.ToolTipText, Qt.white)
dark_palette.setColor(QPalette.Text, Qt.white)
dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
dark_palette.setColor(QPalette.Dark, QColor(35, 35, 35))
dark_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
dark_palette.setColor(QPalette.ButtonText, Qt.white)
dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
dark_palette.setColor(QPalette.BrightText, Qt.red)
dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
dark_palette.setColor(QPalette.HighlightedText, Qt.white)
dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
