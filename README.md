<p align="center">
<img src=https://user-images.githubusercontent.com/11555742/69891714-ec14ca00-12fe-11ea-9140-92842fa1bff9.jpg width=500>
</p>

[![GitHub All Releases](https://img.shields.io/github/downloads/tasmota/tasmotizer/total?style=for-the-badge)](https://github.com/tasmota/tasmotizer/releases)
[![https://pypi.org/project/tasmotizer/](https://img.shields.io/pypi/dw/tasmotizer?logo=pypi&style=for-the-badge)](https://pypi.org/project/tasmotizer)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/tasmota/tasmotizer?style=for-the-badge)](https://github.com/tasmota/tasmotizer/releases)
<a href="https://www.buymeacoffee.com/eYmkLXO" target="_blank"><img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>

The full-featured flashing tool for Tasmota. With the great [ESPtool](https://github.com/espressif/esptool) from Espressif under the hood, and all required settings by default.

## New in 1.3

 - Rewritten and redesigned 'Send config' dialog. Now more readable with even more options!

 - Double-click a config section on the list to toggle its selection, if you don't feel like sniping the checkboxes
 
 - Configuration file is now saved in user directories: `~/.config/tasmota` (Unix/Linux), `C:\Users\User Name\AppData\Roaming\tasmota` (Windows)   
 
 - You can create `templates.txt` in the above directory and fill it with your often used templates (one full template string per line) to easily select them in config dialog

## Features

 - Automatic backup of current ESP image before flashing: in case you want to return to manufacturer firmware
 
 - Flash local .bin images, or simply select from release or development images: it will download them automatically 
 
 - Send configuration to flashed device via serial: one-click configure of Wifi (including recovery AP), MQTT, Module and/or Template  
 
 - Dark theme: proven to increase flashing speed and reliability 
 
## Installation and how to run

 - Option 1: [get Windows  standalone executable](https://github.com/tasmota/tasmotizer/releases) (thanks @Jason2866)<br/>
 _In the odd case of your antivirus going haywire over that application, it's a [false positive](https://github.com/pyinstaller/pyinstaller/issues/3802)._
 
 - Option 2: `pip3 install tasmotizer` and then simply run `tasmotizer.py` from the shell/command line
 
 - Option 3: Clone the repo, `pip3 install PyQt5 pyserial` followed by `python3 tasmotizer.py ` and flash away!
   
 
## Screenshots

<p align="center">
    <img src=https://user-images.githubusercontent.com/11555742/69892658-23d43f80-1308-11ea-8caf-fcd719626f74.png>    
</p>

<p align="center">
    <img src=https://user-images.githubusercontent.com/11555742/69891343-2fba0480-12fc-11ea-9cea-110eb8f65ca2.png>
</p>

(c) 2019 Jacek Ziółkowski https://github.com/jziolkowski
