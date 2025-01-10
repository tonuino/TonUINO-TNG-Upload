from PyQt6.QtCore import QThread, QTime
import time, serial

SER_TIMEOUT = 0.1  

class SerialThread(QThread):
    def __init__(self, portname, baudrate, app):
        QThread.__init__(self)
        self.portname, self.baudrate = portname, baudrate
        self.running = True
        self.app = app
        self.timestamps = app.ui.timestampCheckBox.isChecked()

    def ser_in(self, s):
        if self.timestamps:
            time = QTime.currentTime()
            s = time.toString('hh.mm.ss.zzz - ') + s
        self.app.write(s)
        
    def run(self):
        self.app.write("Opening %s at %u baud" % (self.portname, self.baudrate))
        try:
            self.ser = serial.Serial(self.portname, self.baudrate, timeout=SER_TIMEOUT)
        except:
            self.ser = None
        if not self.ser:
            self.app.write("Can't open port")
            self.running = False
        while self.running:
            s = self.ser.readline(-1)
            if s:
                self.ser_in(s.decode("utf8"))
        if self.ser:
            self.ser.close()
            self.ser = None
            self.app.write("log finished")
            