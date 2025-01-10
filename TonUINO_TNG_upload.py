#!/usr/bin/env python

import sys
from PyQt6.QtWidgets import QApplication

import app
    
def main():
    
    my_app = QApplication(sys.argv)
    tonuinoUploader = app.App()
    tonuinoUploader.show()
    sys.exit(tonuinoUploader.exec())
    
if __name__ == "__main__":
    main()
