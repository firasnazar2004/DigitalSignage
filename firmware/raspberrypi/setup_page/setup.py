from datetime import datetime
from fastapi import FastAPI, APIRouter, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import subprocess
import os
import socket 

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Setup ..")
    yield
    print("Shutting down system")

app = FastAPI(
    title="Digital Signage Setup",
    description="Setup service for new displays to be registered with Dhaher",
    version="1.0.0",
    lifespan=lifespan
)

router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/setup-static", StaticFiles(directory=BASE_DIR), name="setup-static")

app.mount("/setup-static/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")


@app.get("/api/get-ip")
async def get_ip(request: Request):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return {"ip": local_ip}

@app.get("/setup-login")
async def serve_setup_login():
    file_path = os.path.join(BASE_DIR, "setup-login.html")
    print("Serving file:", file_path)
    return FileResponse(file_path)

@app.get("/setup.html")
async def serve_setup():
    file_path = os.path.join(BASE_DIR, "setup.html")
    return FileResponse(file_path)


@router.post('/update-setup-json')
async def update_setup_json(request: Request):
    try:
        data = await request.json()
        config_path = '/home/rasberrybi2/MST/DigitalSignageProject/DigitalSignage/config.json'
        first_time_path = '/home/rasberrybi2/.first_time'

        # Write config
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Remove .first_time
        if os.path.exists(first_time_path):
            os.remove(first_time_path)

        # Log success
        with open('/home/rasberrybi2/setup-debug.log', 'a') as log:
            log.write(f"[{datetime.now()}] Successfully updated config and removed .first_time\n")

        # Reboot (optional, you can comment out for testing)
            subprocess.run(['sudo','reboot'], check=True)

        return {'status':'success'}

    except Exception as e:
        # Log the error
        with open('/home/rasberrybi2/setup-debug.log', 'a') as log:
            log.write(f"[{datetime.now()}] ERROR: {e}\n")
        raise
app.include_router(router)
