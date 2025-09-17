from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager
import webbrowser
import uvicorn
import threading
from backend.app.router import router
from backend.app.db import create_db_and_tables
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv

load_dotenv()

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting Digital Signage ..")
    STORAGE_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")
    os.makedirs(os.path.join(STORAGE_BASE_DIR, "media"), exist_ok=True)
    create_db_and_tables()
    threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:5500/frontend/login.html")).start()  
    yield
    print("Shutting down system")


app = FastAPI(
    title= "Digital Signage Project",
    description='Digital Signage to support both smart and non-smart displays',
    version="1.0.0",
    lifespan=lifespan
    
)

origins = [
    "http://localhost",
    "http://localhost:8080", 
    "http://localhost:5500",  
    "file://", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def read_root_status():
    return {"message" : "Digital Signage Project up and running"}

