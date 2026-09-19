# picture-frame

## Installation on Raspberry Pi

These steps apply for installation on Raspberry Pi 3A+ in September 2026 but should work for other Pis as well:

Install Raspberry Pi OS Lite (e.g. using Raspberry Pi Imager). The following steps assume that there is a user "admin".

Enable and connect wifi

```bash
# If disables, turn on wifi by
 sudo nmcli radio wifi on

# Then enter raspberry pi config menu and connect to a wifi network by
sudo raspi-config
```

Now get the repository and install dependencies

```bash
# Download the repository
curl -L -O https://github.com/hannes005/picture-frame/archive/refs/heads/main.zip

# Unzip
unzip main.zip

# Install dependencies
sudo apt install -y python3-pyqt5 python3-pillow python3-uvicorn python3-fastapi
```

Now we could already run the application by

```bash 
# This starts the web ui
python3 -m uvicorn webui.webui:app --host 0.0.0.0 --port 8000

# THis starts the slideshow
QT_QPA_PLATFORM=eglfs python3 -m slideshow.slideshow
```

Register applications as services to automatically start them after bootup.

Create a service file for the slideshow

```bash
sudo nano /etc/systemd/system/slideshow.service

#Put in the following
[Unit]
Description=Picture Frame Slideshow
After=local-fs.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/picture-frame-main
Environment=QT_QPA_PLATFORM=eglfs
ExecStart=/usr/bin/python3 -m slideshow.slideshow
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create another service file for the webui

```bash
sudo nano /etc/systemd/system/webui.service

#Put in the following
[Unit]
Description=Picture Frame Web UI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/picture-frame-main
ExecStart=/usr/bin/python3 -m uvicorn webui.webui:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Now reload and enable services
```bash
#Reload and Enable services
sudo systemctl daemon-reload
sudo systemctl enable slideshow.service webui.service
```

Reboot the device.