<p align="center">
<img src=https://user-images.githubusercontent.com/11555742/69891714-ec14ca00-12fe-11ea-9140-92842fa1bff9.jpg width=500>
</p>

The full-featured flashing tool for Tasmota. With the great [ESPtool](https://github.com/espressif/esptool) from Espressif under the hood, and all required settings by default.

## Features

 - Automatic backup of current ESP image before flashing: in case you want to return to manufacturer firmware
 
 - Flash local .bin images, or simply select from release or development images: it will download them automatically 
 
 - Send configuration to flashed device via serial: one-click configure of Wifi (including recovery AP), MQTT, Module and/or Template  
 
 - Dark theme: proven to increase flashing speed and reliability 
 
## Installation and how to run

 - Option 1: download and use any of our released binary versions available for Linux, Windows (thanks @Jason2866)
 
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
