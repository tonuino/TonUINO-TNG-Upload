#!/usr/bin/env python

from enum import Enum
import tempfile
import certifi
import ssl
import urllib.request
import shutil
import subprocess
import serial.tools.list_ports
import sys, os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#              V3  V5   V3X3
VAR        =  ["3", "5", "3x3"]

class var_type(Enum):
    V3          = 0
    V5          = 1
    V3X3        = 2

    def get_download_str(self):
        return VAR[self.value]

#              NANO              EVERY             EVERY4808            AIO           AIOPLUS
HW        =  ["TonUINO_Classic", "TonUINO_Every", "TonUINO_Every4808", "ALLinONE",   "ALLinONE_Plus"]

class hw_type(Enum):
    NANO        = 0
    EVERY       = 1
    EVERY_4808  = 2
    AIO         = 3
    AIO_PLUS    = 4

    def get_download_path(self, variant):
        return "https://tonuino.github.io/TonUINO-TNG/" + HW[self.value] + "_" + variant.get_download_str() + "/firmware.hex"

def upload(downlfilename, hwtype, port):
    args = []
    if   hwtype == hw_type.NANO:
        args = ["-patmega328p", "-carduino"  , "-P" + port, "-b57600", "-D", "-Uflash:w:" + downlfilename + ":i"]
    elif hwtype == hw_type.EVERY:
        args = ["-patmega4809", "-cjtag2updi", "-P" + port                 , "-Uflash:w:" + downlfilename + ":i", "-Ufuses:w:0x00,0x54,0x01,0xff,0x00,0b11001001,0x06,0x00,0x00:m", "-Ulock:w:0xC5:m", "-r"]
    elif hwtype == hw_type.EVERY_4808:
        args = ["-patmega4808", "-cjtag2updi", "-P" + port                 , "-Uflash:w:" + downlfilename + ":i", "-Ufuses:w:0x00,0x54,0x01,0xff,0x00,0b11001001,0x06,0x00,0x00:m", "-Ulock:w:0xC5:m"]
    elif hwtype == hw_type.AIO:
        args = ["-patmega328p", "-carduino"  , "-P" + port, "-b57600", "-D", "-Uflash:w:" + downlfilename + ":i"]
    elif hwtype == hw_type.AIO_PLUS:
        args = ["-patmega4809", "-carduino"  , "-P" + port, "-b115200","-D", "-Uflash:w:" + downlfilename + ":i"]
    else:
        print("Oops")
        return
    
    print([resource_path("avrdude")] + args) 
    subprocess.run([resource_path("avrdude")] + args) 

def download(downlfilename, hwtype, variant):
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(hwtype.get_download_path(variant), context=context) as f_in:
        with open(downlfilename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    print("downloaded " + hwtype.get_download_path(variant) + " to " + downlfilename)
   
def select(descr, l):
    print()
    print("###########################")
    i = 0
    for ll in l:
        print(i, ll)
        i = i+1
    ok = False
    while not ok:
        ret = int(input("Bitte wähle {} [0..{}]: ".format(descr, i-1)))
        if ret >= 0 and ret < i:
            ok = True
    print(l[ret])
    return ret
        
    
def main():
    
    print()
    print("###########################")
    print("# TonUINO online Uploader #")
    print("###########################")

    downldir = tempfile.TemporaryDirectory()
    downlfilename = downldir.name + "/firmware.hex"
    
    hwtype  = hw_type(select("den Hardware Type", HW))
    variant = var_type(select("die Variante", VAR))
    
    ports = serial.tools.list_ports.comports()

    used_ports = []
    for port, desc, hwid in sorted(ports):
        if desc != "n/a":
            used_ports.append((port,desc))
    port = used_ports[select("den Port", used_ports)][0]

    print()
    print("###########################")
    print("# Download vom Github     #")
    print("###########################")

    download(downlfilename, hwtype, variant)

    print()
    print("###########################")
    print("# Upload zum TonUINO      #")
    print("###########################")

    upload(downlfilename, hwtype, port)

    print()
    print("finished...")

if __name__ == "__main__":
    main()
