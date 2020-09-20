from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QSizePolicy, QGroupBox, QSpinBox, QHBoxLayout, QDialog, QProgressBar, \
    QPushButton, QButtonGroup, QDialogButtonBox, QLabel, QFrame, QProgressDialog


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


dark_palette = QPalette()
dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
dark_palette.setColor(QPalette.WindowText, Qt.white)
dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))
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