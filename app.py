
from PyQt6.QtCore import pyqtSignal, QProcess
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
        
        for port, desc in self.used_ports:
            self.ui.portCheckBox.addItem(port + " - " + desc)

        self.ui.refreshPortPushButton.clicked.connect(self.on_refreshPortPushButton_clicked)
        self.ui.startPushButton.clicked.connect(self.on_startPushButton_clicked)
        self.ui.downloadSD.clicked.connect(self.on_downloadSDPushButton_clicked)
        self.ui.consolePushButton.clicked.connect(self.on_consolePushButton_toggle)
       

        self.console_update.connect(self.append_console)
        
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.process_stderr_ready)
        self.process.readyReadStandardOutput.connect(self.process_stdout_ready)
        self.process.started.connect(lambda: self.startPushButton.setEnabled(False))
        self.process.finished.connect(lambda: self.startPushButton.setEnabled(True))
        
        self.serialThread = None
        

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
        else: 
            self.serialThread.running = False
            self.serialThread.wait()
            self.serialThread = None
            self.ui.timestampCheckBox.setEnabled(True)
            
    def on_startPushButton_clicked(self):
        self.ui.console.clear()
        if len(self.used_ports) == 0:
            self.ui.console.append("Kein USB Port gefunden")
            self.ui.consolePushButton.setChecked(False)
            return

        hwtype = utils.hw_type(self.hwTypeCheckBox.currentIndex())
        variant = utils.var_type(self.hwVariantCheckBox.currentIndex())
        port = self.used_ports[self.portCheckBox.currentIndex()][0]
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

        