from datetime import datetime
from time import sleep

import serial
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from esptool import esptool as esptool


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