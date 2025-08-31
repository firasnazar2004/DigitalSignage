from fastapi import FastAPI
from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status, Form 
from contextlib import asynccontextmanager
import json
from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Starting Setup ..")
    yield
    print("Shutting down system")

app = FastAPI(
    title= "Digital Signage Setup",
    description='Setup service for new displays to be registered with Dhaher',
    version="1.0.0",
    lifespan=lifespan
)

router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@router.post('/update-setup-json')
async def update_setup_json(request:Request): 
    data= await request.json()
    with open('setup.json','w') as f:
        json.dump(data,f,indent=2)
    return {'status':'success'}

app.include_router(router)