# Raspberry Pi Installation Guide

Simple guide to help with Raspberry Pi installation for Digital Signage Solution.


## Folder Structure
/ home / {user} / MST / DigitalSignageProject / DigitalSignage / 
```bash

|-- client.py
|-- config.json
|-- __init__.py
|-- Media (stores the downloaded media)
|   
|-- __pycache__
|   
|-- Setup (contains the backend+frontend to run setup service for first time)
|   |-- assets
|   |-- __init__.py
|   |-- old
|   |-- __pycache__
|   |-- restart_service.sh
|   |-- setup.html
|   |-- setup.json
|   |-- setup-login.html
|   `-- setup.py
|-- start-slideshow.sh (shell script for starting slideshow)
`-- venv
    |-- bin
    |-- include
    |-- lib
    |-- lib64 -> lib
    `-- pyvenv.cfg


```
## Dependencies
Install the dependencies using
```python
pip install dependencies.txt
```
dependencies.txt:

```bash
Package            Version
------------------ --------
annotated-types    0.7.0
anyio              4.10.0
certifi            2025.8.3
charset-normalizer 3.4.2
click              8.2.1
fastapi            0.116.1
h11                0.16.0
idna               3.10
pip                23.0.1
pydantic           2.11.7
pydantic_core      2.33.2
requests           2.32.4
setuptools         66.1.1
sniffio            1.3.1
starlette          0.47.3
typing_extensions  4.15.0
typing-inspection  0.4.1
urllib3            2.5.0
```

## Start-Slideshow.sh

```bash
#!/bin/bash

# Allow other processes to connect to the X server
/usr/bin/xhost +


# Start the Python client script
/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/venv/bin/python /home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/client.py

```

## Digital-Signage.service

Service that runs start-slideshow.sh shown above, provided that the condition of .first_time file not being present is true. The .first_time is a simple, empty file that the system checks for each time during booting; if the file exists, then the setup-digital-signange.service (in the next section) is started, if not then this service is started.

```bash
[Unit]
Description=Digital Signage Slideshow
After=graphical-session.target
ConditionPathExists=!/home/rasberrybi2/.first_time

[Service]
ExecStart=/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/start-slideshow.sh
WorkingDirectory=/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage
Environment=DISPLAY=:0
Restart=always

[Install]
WantedBy=default.target
```
## Setup-Digital-Signage.service
As explained, if the condition is met, then this service will start the simple backend to allow the setup page to be accessed from other devices on the network.

```bash
[Unit]
Description=Digital Signage Setup Service
After=graphical-session.target network-online.target
ConditionPathExists=/home/rasberrybi2/.first_time

[Service]
WorkingDirectory=/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/Setup
Environment=DISPLAY=:0
ExecStart=/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/venv/bin/python -m uvicorn setup:app --host 0.0.0.0 --port 5500
ExecStartPost=/usr/bin/chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5500/setup-static/setup-login.html
Restart=on-failure

[Install]
WantedBy=default.target
```
