<p align="center">
<img src=https://user-images.githubusercontent.com/11555742/69891714-ec14ca00-12fe-11ea-9140-92842fa1bff9.jpg width=500>
</p>

[![GitHub All Releases](https://img.shields.io/github/downloads/tasmota/tasmotizer/total?style=for-the-badge)](https://github.com/tasmota/tasmotizer/releases)
[![https://pypi.org/project/tasmotizer/](https://img.shields.io/pypi/dw/tasmotizer?logo=pypi&style=for-the-badge)](https://pypi.org/project/tasmotizer)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/tasmota/tasmotizer?style=for-the-badge)](https://github.com/tasmota/tasmotizer/releases)
[![https://www.buymeacoffee.com/eYmkLXO](https://img.shields.io/badge/Donate-Buy%20me%20a%20coffee-orange?style=for-the-badge)](https://www.buymeacoffee.com/eYmkLXO)

The full-featured ESP8266 flashing tool for [Tasmota](https://github.com/arendst/Tasmota). With the great [ESPtool](https://github.com/espressif/esptool) from Espressif under the hood, and all required settings by default.

## Features

 - Automatic backup of current ESP image before flashing: in case you want to return to manufacturer firmware<br/>
 Now supporting backup sizes up to 16MB
 
 - Flash local .bin images, or simply select from release or development images: it will download them automatically 
 
 - Send configuration to flashed device via serial: one-click configure of Wifi (including recovery AP), MQTT, Module and/or Template  
 
 - Single-click get the IP of your device (DISCLAIMER: this functionality depends on the current state of your device, so it might require a few tries to get the proper result)
 
 - Dark theme: proven to increase flashing speed and reliability 
 
## Installation and how to run

 - Option 1: [get Windows  standalone executable](https://github.com/tasmota/tasmotizer/releases) (thanks @Jason2866):<br/>
 `tasmotizer.exe` (64bit)<br/>
 `tasmotizer-x86.exe` (32bit)<br/>
 In the odd case of your antivirus going haywire over that application, it's a [false positive](https://github.com/pyinstaller/pyinstaller/issues/3802).
 
 - Option 2: Install from PyPI using pip:<br/>
 Upgrade pip and wheel packages: `pip3 install --upgrade pip wheel`<br/>
 Install tasmotizer: `pip3 install tasmotizer`   
 Then simply run `tasmotizer.py` or `python3 -m tasmotizer.py` from the shell/command line
 
 - Option 3: Clone the repo, `pip3 install -r requirements.txt` followed by `python3 tasmotizer.py ` and flash away!
 
## Screenshots

<p align="center">
    <img src=https://user-images.githubusercontent.com/24528715/93748447-96e0d680-fbf8-11ea-9647-9d303cda0ea7.png>    
</p>

<p align="center">
    <img src=https://user-images.githubusercontent.com/24528715/93748408-82044300-fbf8-11ea-89c5-891065e52430.png>
</p>

(c) 2019 Jacek Ziółkowski https://github.com/jziolkowski
