#!/usr/bin/env python
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from gui.tasmotizer import Tasmotizer
from gui import banner, dark_palette


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
