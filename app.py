
from PyQt6.QtCore import pyqtSignal, QProcess, Qt, QFile
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import QDialog, QFileDialog
from PyQt6 import uic
import utils, console_thread
import tempfile
#import gui

class App(QDialog):
    console_update = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(App, self).__init__(parent)

        self.downldir = tempfile.TemporaryDirectory()
        self.used_ports = utils.get_used_ports()

        self.ui = uic.loadUi(utils.resource_path('gui.ui'), self)
        #self.ui = gui.Ui_TonUINOUploader()
        #self.ui.setupUi(self)

        self.ui.hwTypeCheckBox.addItems(utils.HW_des)
        self.ui.hwVariantCheckBox.addItems(utils.VAR_desc)
        self.ui.hwVariantCheckBox.setItemData(utils.var_type.File.value, 0, Qt.ItemDataRole.UserRole - 1)
        
        for port, desc in self.used_ports:
            self.ui.portCheckBox.addItem(port + " - " + desc)

        self.ui.refreshPortPushButton.clicked.connect(self.on_refreshPortPushButton_clicked)
        self.ui.startPushButton.clicked.connect(self.on_startPushButton_clicked)
        self.ui.downloadSD.clicked.connect(self.on_downloadSDPushButton_clicked)
        self.ui.consolePushButton.clicked.connect(self.on_consolePushButton_toggle)
        self.ui.localFileLineEdit.textChanged.connect(self.on_localFileLineEdit_changed)
        self.ui.localFileToolButton.clicked.connect(self.on_localFileToolButton_clocked)
       

        self.console_update.connect(self.append_console)
        
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.process_stderr_ready)
        self.process.readyReadStandardOutput.connect(self.process_stdout_ready)
        self.process.started.connect(lambda: self.ui.startPushButton.setEnabled(False))
        self.process.started.connect(lambda: self.ui.consolePushButton.setEnabled(False))
        self.process.finished.connect(lambda: self.ui.startPushButton.setEnabled(True))
        self.process.finished.connect(lambda: self.ui.consolePushButton.setEnabled(True))
        
        self.serialThread = None
        
        self.ui.hwTypeCheckBox.setFocus()

    def write(self, text):
        self.console_update.emit(text)

    def append_console(self, text):
        cur = self.ui.console.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(str(text))
        self.ui.console.setTextCursor(cur)
        
    def process_stderr_ready(self):
        self.append_console(self.process.readAllStandardError().data().decode('utf8'))

    def process_stdout_ready(self):
        self.append_console(self.process.readAllStandardOutput().data().decode('utf8'))

    def closeEvent(self, event):
        if self.serialThread != None:
            self.serialThread.running = False
            self.serialThread.wait()

    def on_consolePushButton_toggle(self, checked):
        if checked:
            self.ui.console.clear()
            if len(self.used_ports) == 0:
                self.ui.console.append("Kein USB Port gefunden")
                self.ui.consolePushButton.setChecked(False)
                return
            port = self.used_ports[self.ui.portCheckBox.currentIndex()][0]
            self.serialThread = console_thread.SerialThread(port, 115200, self)
            self.serialThread.start()
            self.ui.timestampCheckBox.setEnabled(False)
            self.ui.startPushButton.setEnabled(False)
        else: 
            self.serialThread.running = False
            self.serialThread.wait()
            self.serialThread = None
            self.ui.timestampCheckBox.setEnabled(True)
            self.ui.startPushButton.setEnabled(True)
            
    def on_startPushButton_clicked(self):
        self.ui.console.clear()
        if len(self.used_ports) == 0:
            self.ui.console.append("Kein USB Port gefunden")
            self.ui.consolePushButton.setChecked(False)
            return

        hwtype = utils.hw_type(self.hwTypeCheckBox.currentIndex())
        variant = utils.var_type(self.hwVariantCheckBox.currentIndex())
        port = self.used_ports[self.portCheckBox.currentIndex()][0]
        
        if variant == utils.var_type.File:
            utils.upload(self.ui.console, self.localFileLineEdit.text(), hwtype, port, self.process)
        else:
            utils.download_upload(self.ui.console, self.downldir, hwtype, variant, port, self.process)
        
    def on_downloadSDPushButton_clicked(self):
        dirname = QFileDialog.getExistingDirectory(
        self,
        "Wähle das Verzeichnis zum Speichern des zip Files",
        options=QFileDialog.Option.DontUseNativeDialog)
        if dirname != "":
            self.ui.console.clear()
            utils.download_sd(self.ui.console, dirname)
        
    def on_refreshPortPushButton_clicked(self):
        used_ports = utils.get_used_ports()
        if used_ports != self.used_ports:
            self.used_ports = used_ports
            self.ui.portCheckBox.clear()
            for port, desc in self.used_ports:
                self.ui.portCheckBox.addItem(port + " - " + desc)

    def on_localFileLineEdit_changed(self, filename):
        if filename.endswith(".hex") and QFile(filename).exists():
            self.ui.hwVariantCheckBox.setItemData(utils.var_type.File.value, 33, Qt.ItemDataRole.UserRole - 1)
            self.ui.hwVariantCheckBox.setCurrentIndex(self.ui.hwVariantCheckBox.count()-1)
        else:
            self.ui.hwVariantCheckBox.setItemData(utils.var_type.File.value, 0, Qt.ItemDataRole.UserRole - 1)
            self.ui.hwVariantCheckBox.setCurrentIndex(0)
        
    def on_localFileToolButton_clocked(self):
        filename = QFileDialog.getOpenFileName(
        self, 
        "Wähle das lokale Firmware File",
        ".",
        "Fimware (*.hex)",
        options=QFileDialog.Option.DontUseNativeDialog)
        self.ui.localFileLineEdit.setText(filename[0])

            
        