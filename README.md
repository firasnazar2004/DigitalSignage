# Digital Signage Management System  

  
![Logo](frontend/assets/logo-white.svg)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)  
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)  
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)  


A cloud-connected platform for managing digital signage content across multiple displays. Designed for scalability, flexibility, and compatibility with both smart TVs and non-smart displays powered by Raspberry Pi.  
  
---

## Table of Contents  

- [Overview](#overview)  
- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Repository Structure](#repository-structure)  
- [API Endpoints](#api-endpoints)  
- [Getting Started](#getting-started)  
- [Planned Improvements](#planned-improvements)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Overview  

This system integrates **five major components**:  

1. **Frontend** – A web interface to upload media, register displays, and configure settings.  
2. **Backend (Cloud API)** – A FastAPI-powered server for handling media uploads, display registration, authentication, and status checks.  
3. **File Storage** – Stores media files in the cloud (e.g., S3, local disk).  
4. **Database** – Tracks displays, uploaded media, and media-display mappings.  
5. **Displays (Smart TVs or Raspberry Pi)** – Devices periodically sync with the backend to download and play assigned content.  

---

## Features  

- Upload and manage images, videos, and other media.  
- Register and authenticate new displays with unique API keys.  
- Automatic media sync on each display.  
- Support for both smart and Raspberry Pi-powered displays.  
- Systemd service for auto-start on boot.  

---

## Tech Stack  

| Layer         | Technology                     |  
|---------------|--------------------------------|  
| Frontend      | HTML (expandable to React/Vue) |  
| Backend API   | FastAPI (Python)               |  
| File Storage  | Cloud / Local file system      |  
| Database      | SQLite / PostgreSQL            |  
| Display Agent | Python client (Raspberry Pi)   |  
| Services      | systemd (auto-start)           |  

---

## Repository Structure  
├── .venv/                       # Python virtual environment
├── backend/
│   └── app/
│       ├── pycache/
│       ├── storage/            # (Planned) Media storage utilities
│       ├── db.py               # DB models and connection
│       ├── main.py             # FastAPI app entry point
│       ├── models.py           # Pydantic schemas
│       ├── router.py           # API route handlers
│       └── test.py             # Basic testing and endpoints
├── firmware/
│   ├── client.py               # Script running on display (e.g. Raspberry Pi)
│   ├── config.json             # Device config (API key, display ID)
│   ├── digital-signage.service # systemd service for auto-start
│   └── reboot-slideshow-instructions.txt # Setup instructions
├── frontend/
│   ├── dhaher.html
│   └── login.html

---

## API Endpoints  

- **POST /media** – Upload and configure media (image, video, carousel, etc.)  
- **POST /displays** – Register a new display (API key generated)  
- **GET /status/{display_id}** – Display checks if new media is available  
- **GET /media/{media_id}** – Display downloads assigned media file  

Each display authenticates using its unique API key. Admin routes for frontend users will also be protected.  

---

## Getting Started  

### Prerequisites  

- Python 3.9+  
- Virtual environment (`venv`)  
- SQLite or PostgreSQL  

### Installation  

```bash
# Clone the repo
git clone https://github.com/firasnazar2004/digital-signage-system.git

# Backend setup
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Firmware (on Raspberry Pi)
cd firmware
sudo systemctl --user start digital-signage.service
```

## Planned Improvements
- Support media previews and scheduling.
- Expand media types (e.g., playlists, carousels).
- Integrate cloud storage (AWS S3, Firebase).
- WebSocket/MQTT support for real-time updates.  