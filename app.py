
from PyQt6.QtCore import pyqtSignal, QProcess
from PyQt6.QtGui import (QFont, QTextCursor)
from PyQt6.QtWidgets import (QDialog, QGridLayout, QGroupBox, QPushButton, QComboBox, QTextEdit, QLabel, QVBoxLayout,
    QCheckBox)
import utils, console_thread
import tempfile

class App(QDialog):
    console_update = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super(App, self).__init__(parent)

        self.downldir = tempfile.TemporaryDirectory()
        self.used_ports = utils.get_used_ports()

        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()
        self.createConsole()

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.topLeftGroupBox, 0, 0)
        mainLayout.addWidget(self.topRightGroupBox, 0, 2)
        mainLayout.addWidget(self.console, 1, 0, 1, 3)
        mainLayout.setRowStretch(0, 1)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("TonUINO-TNG upload")
        
        self.console_update.connect(self.append_console)
        
        self.process = QProcess(self)
        self.process.readyReadStandardError.connect(self.process_stderr_ready)
        self.process.readyReadStandardOutput.connect(self.process_stdout_ready)
        self.process.started.connect(lambda: self.startPushButton.setEnabled(False))
        self.process.finished.connect(lambda: self.startPushButton.setEnabled(True))
        
        self.serialThread = None
        

    def createTopLeftGroupBox(self):
        self.topLeftGroupBox = QGroupBox("")

        hwTypeLabel = QLabel("Hardware Type:")
        self.hwTypeCheckBox = QComboBox()
        self.hwTypeCheckBox.addItems(utils.HW_des)

        hwVariantLabel = QLabel("Hardware Variante:")
        self.hwVariantCheckBox = QComboBox()
        self.hwVariantCheckBox.addItems(utils.VAR_desc)

        portLabel = QLabel("Port:")
        self.portCheckBox = QComboBox()
        for port, desc in self.used_ports:
            self.portCheckBox.addItem(port + " - " + desc)

        self.refreshPortPushButton = QPushButton("Refresh Ports")
        self.refreshPortPushButton.setDefault(True)
        self.refreshPortPushButton.clicked.connect(self.on_refreshPortPushButton_clicked)

        layout = QVBoxLayout()
        layout.addWidget(hwTypeLabel)
        layout.addWidget(self.hwTypeCheckBox)
        layout.addWidget(hwVariantLabel)
        layout.addWidget(self.hwVariantCheckBox)
        layout.addWidget(portLabel)
        layout.addWidget(self.portCheckBox)
        layout.addWidget(self.refreshPortPushButton)
        layout.addStretch(1)
        self.topLeftGroupBox.setLayout(layout)

    def createTopRightGroupBox(self):
        self.topRightGroupBox = QGroupBox("")

        self.startPushButton = QPushButton("Start Upload Firmware")
        self.startPushButton.setDefault(True)
        self.startPushButton.clicked.connect(self.on_startPushButton_clicked)

        self.consolePushButton = QPushButton("Konsole Log")
        self.consolePushButton.setCheckable(True)
        self.consolePushButton.setChecked(False)
        self.consolePushButton.clicked.connect(self.on_consolePushButton_toggle)

        self.timestampCheckBox = QCheckBox("Timestamps")
        self.timestampCheckBox.setChecked(False)

        layout = QVBoxLayout()
        layout.addWidget(self.startPushButton)
        layout.addStretch(1)
        layout.addWidget(self.consolePushButton)
        layout.addWidget(self.timestampCheckBox)
        self.topRightGroupBox.setLayout(layout)

    def createConsole(self):
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMinimumSize(1000, 600)
        font = QFont()
        font.setFamily("Courier New")
        font.setPointSize(10)
        self.console.setFont(font)

    def write(self, text):
        self.console_update.emit(text)

    def append_console(self, text):
        cur = self.console.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.insertText(str(text))
        self.console.setTextCursor(cur)
        
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
            self.console.clear()
            if len(self.used_ports) == 0:
                self.console.append("TonUINO ist mit keinem USB port verbunden")
                self.consolePushButton.setChecked(False)
                return
            port = self.used_ports[self.portCheckBox.currentIndex()][0]
            self.serialThread = console_thread.SerialThread(port, 115200, self)
            self.serialThread.start()
            self.timestampCheckBox.setEnabled(False)
        else: 
            self.serialThread.running = False
            self.serialThread.wait()
            self.serialThread = None
            self.timestampCheckBox.setEnabled(True)
            
    def on_startPushButton_clicked(self):
        self.console.clear()
        if len(self.used_ports) == 0:
            self.console.append("TonUINO ist mit keinem USB port verbunden")
            self.consolePushButton.setChecked(False)
            return

        hwtype = utils.hw_type(self.hwTypeCheckBox.currentIndex())
        variant = utils.var_type(self.hwVariantCheckBox.currentIndex())
        port = self.used_ports[self.portCheckBox.currentIndex()][0]
        utils.download_upload(self.console, self.downldir, hwtype, variant, port, self.process)
        
    def on_refreshPortPushButton_clicked(self):
        used_ports = utils.get_used_ports()
        if used_ports != self.used_ports:
            self.used_ports = used_ports
            self.portCheckBox.clear()
            for port, desc in self.used_ports:
                self.portCheckBox.addItem(port + " - " + desc)

        