from enum import Enum
import certifi
import ssl
import urllib.request
import shutil
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

VAR        =  ["3"       , "5"       , "3x3"             , "5f"                   , "File -->"]
VAR_desc   =  ["3 Tasten", "5 Tasten", "3x3 Button Board", "5 Tasten alle Feature", "File -->"]

class var_type(Enum):
    V3          = 0
    V5          = 1
    V3X3        = 2
    V5F         = 3
    File        = 4

    def get_download_str(self):
        return VAR[self.value]

#              NANO               NANO_NEW                          EVERY            EVERY4808            AIO           AIOPLUS
HW        =  ["TonUINO_Classic", "TonUINO_Classic"               , "TonUINO_Every", "TonUINO_Every4808", "ALLinONE",   "ALLinONE_Plus"]
HW_des    =  ["TonUINO Classic", "TonUINO Classic new Bootloader", "TonUINO Every", "TonUINO Every4808", "ALLinONE",   "ALLinONE Plus"]

class hw_type(Enum):
    NANO        = 0
    NANO_NEW    = 1
    EVERY       = 2
    EVERY_4808  = 3
    AIO         = 4
    AIO_PLUS    = 5

    def get_download_path(self, variant):
        return "https://tonuino.github.io/TonUINO-TNG/" + HW[self.value] + "_" + variant.get_download_str() + "/firmware.hex"

compatibility = [
#    3   5   3x3 5f
    [1,  1,  1,  0], #  NANO      
    [1,  1,  1,  0], #  NANO_NEW      
    [1,  1,  1,  1], #  EVERY     
    [1,  1,  1,  1], #  EVERY_4808
    [1,  1,  1,  0], #  AIO       
    [1,  1,  1,  1]  #  AIO_PLUS  
    ]

def get_used_ports():
    ports = serial.tools.list_ports.comports()

    used_ports = []
    for port, desc, hwid in sorted(ports):
        if desc != "n/a":
            used_ports.append((port,desc))
    return used_ports

def calculate_code_size(console, hex_file_path):
    code_size = 0
    try:
        with open(hex_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith(':'):
                    data_length = int(line[1:3], 16)
                    record_type = int(line[7:9], 16)
                    if record_type == 0x00:
                        code_size += data_length

    except FileNotFoundError:
        console.append(f"Die Datei '{hex_file_path}' wurde nicht gefunden.")
    except Exception as e:
        console.append(f"Ein Fehler ist aufgetreten: {e}")

    return code_size


def upload(console, downlfilename, hwtype, port, process):
    code_size = calculate_code_size(console, downlfilename)
    if code_size == 0:
        return 
    max_code_size = 0;
    args = []
    if   hwtype == hw_type.NANO:
        args = ["-patmega328p", "-carduino"  , "-P" + port, "-b57600", "-D", "-Uflash:w:" + downlfilename + ":i"]
        max_code_size = 30720
    elif hwtype == hw_type.NANO_NEW:
        args = ["-patmega328p", "-carduino"  , "-P" + port, "-b115200","-D", "-Uflash:w:" + downlfilename + ":i"]
        max_code_size = 30720
    elif hwtype == hw_type.EVERY:
        args = ["-patmega4809", "-cjtag2updi", "-P" + port                 , "-Uflash:w:" + downlfilename + ":i", "-Ufuses:w:0x00,0x54,0x01,0xff,0x00,0b11001001,0x06,0x00,0x00:m", "-Ulock:w:0xC5:m", "-r"]
        max_code_size = 49152
    elif hwtype == hw_type.EVERY_4808:
        args = ["-patmega4808", "-cjtag2updi", "-P" + port                 , "-Uflash:w:" + downlfilename + ":i", "-Ufuses:w:0x00,0x54,0x01,0xff,0x00,0b11001001,0x06,0x00,0x00:m", "-Ulock:w:0xC5:m"]
        max_code_size = 49152
    elif hwtype == hw_type.AIO:
        args = ["-patmega328p", "-carduino"  , "-P" + port, "-b57600", "-D", "-Uflash:w:" + downlfilename + ":i"]
        max_code_size = 29696
    elif hwtype == hw_type.AIO_PLUS:
        args = ["-patmega4809", "-carduino"  , "-P" + port, "-b115200","-D", "-Uflash:w:" + downlfilename + ":i"]
        max_code_size = 48640
    else:
        console.append("Oops")
        return
    
    if code_size > max_code_size:
        console.append(f"Die Datei '{downlfilename}' (Code Größe {code_size}) ist zu groß für die HW. Die maximale Größe ist {max_code_size}.")
        return
    
    console.append(resource_path("avrdude") + ' ' + ' '.join(args)) 
    console.append("\n#################################################################################\n")
    process.start(resource_path("avrdude"), args) 

def download(console, downlfilename, hwtype, variant):
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(hwtype.get_download_path(variant), context=context) as f_in:
        with open(downlfilename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    console.append("downloaded " + hwtype.get_download_path(variant) + " to " + downlfilename)
   
def download_upload(console, downldir, hwtype,variant, port, process):
    downlfilename = os.path.join(downldir.name, "firmware.hex")
    
    download(console, downlfilename, hwtype, variant)
    console.append("\n#################################################################################\n")
    upload(console, downlfilename, hwtype, port, process)
   
def download_sd(console, dirname):
    url = "https://tonuino.github.io/TonUINO-TNG/sd-card.zip"
    filename = os.path.join(dirname, "sd-card.zip")
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=context) as f_in:
        with open(filename, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    console.append("downloaded " + url + " to " + filename)


