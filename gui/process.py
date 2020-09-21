from PyQt5.QtCore import QUrl, QThread, pyqtSlot
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QDialog, QFormLayout, QProgressBar, QDialogButtonBox, QStatusBar, QMessageBox, QApplication

from gui.widgets import VLayout
from esptool import ESPWorker, esptool
from utils import NetworkError


class ProcessDialog(QDialog):
    def __init__(self, port, **kwargs):
        super().__init__()

        self.setWindowTitle('Tasmotizing...')
        self.setFixedWidth(400)

        self.exception = None

        esptool.sw.progress.connect(self.update_progress)

        self.nam = QNetworkAccessManager()
        self.nrBinFile = QNetworkRequest()
        self.bin_data = b''

        self.setLayout(VLayout(5, 5))
        self.actions_layout = QFormLayout()
        self.actions_layout.setSpacing(5)

        self.layout().addLayout(self.actions_layout)

        self._actions = []
        self._action_widgets = {}

        self.port = port

        self.auto_reset = kwargs.get('auto_reset', False)

        self.file_path = kwargs.get('file_path')
        if self.file_path and self.file_path.startswith('http'):
            self._actions.append('download')

        self.backup = kwargs.get('backup')
        if self.backup:
            self._actions.append('backup')
            self.backup_size = kwargs.get('backup_size')

        self.erase = kwargs.get('erase')
        if self.erase:
            self._actions.append('erase')

        if self.file_path:
            self._actions.append('write')

        self.create_ui()
        self.start_process()

    def create_ui(self):
        for action in self._actions:
            pb = QProgressBar()
            pb.setFixedHeight(35)
            self._action_widgets[action] = pb
            self.actions_layout.addRow(action.capitalize(), pb)

        self.btns = QDialogButtonBox(QDialogButtonBox.Abort)
        self.btns.rejected.connect(self.abort)
        self.layout().addWidget(self.btns)

        self.sb = QStatusBar()
        self.layout().addWidget(self.sb)

    def appendBinFile(self):
        self.bin_data += self.bin_reply.readAll()

    def saveBinFile(self):
        if self.bin_reply.error() == QNetworkReply.NoError:
            self.file_path = self.file_path.split('/')[-1]
            with open(self.file_path, 'wb') as f:
                f.write(self.bin_data)
            self.run_esp()
        else:
            raise NetworkError

    def updateBinProgress(self, recv, total):
        self._action_widgets['download'].setValue(recv//total*100)

    def download_bin(self):
        self.nrBinFile.setUrl(QUrl(self.file_path))
        self.bin_reply = self.nam.get(self.nrBinFile)
        self.bin_reply.readyRead.connect(self.appendBinFile)
        self.bin_reply.downloadProgress.connect(self.updateBinProgress)
        self.bin_reply.finished.connect(self.saveBinFile)

    def show_connection_state(self, state):
        self.sb.showMessage(state, 0)

    def run_esp(self):
        params = {
            'file_path': self.file_path,
            'auto_reset': self.auto_reset,
            'erase': self.erase
        }

        if self.backup:
            params['backup_size'] = self.backup_size

        self.esp_thread = QThread()
        self.esp = ESPWorker(
            self.port,
            self._actions,
            **params
        )
        esptool.sw.connection_state.connect(self.show_connection_state)
        self.esp.waiting.connect(self.wait_for_user)
        self.esp.done.connect(self.accept)
        self.esp.error.connect(self.error)
        self.esp.moveToThread(self.esp_thread)
        self.esp_thread.started.connect(self.esp.run)
        self.esp_thread.start()

    def start_process(self):
        if 'download' in self._actions:
            self.download_bin()
            self._actions = self._actions[1:]
        else:
            self.run_esp()

    def update_progress(self, action, value):
        self._action_widgets[action].setValue(value)

    @pyqtSlot()
    def wait_for_user(self):
        dlg = QMessageBox.information(self,
                                      'User action required',
                                      'Please power cycle the device, wait a moment and press OK',
                                      QMessageBox.Ok | QMessageBox.Cancel)
        if dlg == QMessageBox.Ok:
            self.esp.continue_ok()
        elif dlg == QMessageBox.Cancel:
            self.esp.abort()
            self.esp.continue_ok()
            self.abort()

    def stop_thread(self):
        self.esp_thread.wait(2000)
        self.esp_thread.exit()

    def accept(self):
        self.stop_thread()
        self.done(QDialog.Accepted)

    def abort(self):
        self.sb.showMessage('Aborting...', 0)
        QApplication.processEvents()
        self.esp.abort()
        self.stop_thread()
        self.reject()

    def error(self, e):
        self.exception = e
        self.abort()

    def closeEvent(self, e):
        self.stop_thread()