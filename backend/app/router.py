from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status, Form
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from uuid import uuid4, UUID
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import List, Optional, Annotated, Dict, Any
from datetime import datetime , timedelta   
from sqlmodel import Session, select, col, delete
from fastapi.security import APIKeyHeader
from backend.app.models import Display, DisplayPlaylist, Media, PlaylistMediaLink, User , verify_password, get_password_hash
from backend.app.db import get_session
import hashlib
from . import storage
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from jose import JWTError, jwt 

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
SECRET_KEY = "402511c7e38c4ebd1812a20af2c8c3a618bfe2037d50446db1f0dedac3e8e06d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# ---------------- Models ----------------

class Token(BaseModel):
    access_token : str 
    token_type: str 




class RegisterDisplayRequest(BaseModel):
    name : str
    mac: str
    location: str

class UploadMediaResponse(BaseModel):
    message: str
    media_id: UUID
    media_type: str
    size: int
    assigned_displays: List[UUID] = []
    # MODIFIED: ADD THE OVERRIDE FLAG TO THE RESPONSE MODEL
    override : bool

class AssignMediaRequest(BaseModel):
    display__uuid: UUID
    media_ids: List[UUID]

class BulkMarkDownloadedRequest(BaseModel):
    media_ids : List[UUID]




# ---------------- Storage & Allowed MIME ----------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_BASE_DIR = os.path.join(CURRENT_DIR, "storage")
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml",
    "video/mp4", "video/webm", "video/ogg", "video/x-msvideo"
}
STORAGE_PATH = os.path.join(STORAGE_BASE_DIR, "media")

router = APIRouter()

# ---------------- Dependencies ----------------
async def get_display_by_api_key(api_key: str = Depends(api_key_header), session: Session = Depends(get_session)):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-KEY header missing")
    display = session.exec(select(Display).where(col(Display.api_key) == api_key)).first()
    if not display:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    return display

def create_access_token(data: dict, expires_delta : Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode , SECRET_KEY , algorithm= ALGORITHM)
    return encoded_jwt 


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)] , session: Session = Depends(get_session) ): 
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try: 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username : str = payload.get("sub")
        if username is None: 
            raise credentials_exception
    except JWTError: 
        raise credentials_exception
    
    user = session.exec(select(User).where(User.username == username) ).first()
    if user is None: 
        raise credentials_exception
    return user

# ---------------- Endpoints ----------------
@router.get('/')
def root():
    return {"message": "Digital Signage", "status": "running"}

@router.post("/register")
async def register_display(display_data: RegisterDisplayRequest, session: Session = Depends(get_session)):
    name = display_data.name
    mac = display_data.mac
    location = display_data.location
    existing_display = session.exec(select(Display).where(col(Display.mac) == mac)).first()
    if existing_display:
        existing_playlist = session.exec(select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == existing_display.uuid)).first()
        if not existing_playlist:
            new_playlist = DisplayPlaylist(display_uuid=existing_display.uuid, current_index=0)
            session.add(new_playlist)
            session.commit()
            session.refresh(new_playlist)
        return {"uuid": existing_display.uuid, "message": "Display already registered", "api_key": existing_display.api_key}
    new_display = Display(name= name, mac=mac, location=location)
    session.add(new_display)
    session.commit()
    session.refresh(new_display)
    new_playlist = DisplayPlaylist(display_uuid=new_display.uuid, current_index=0)
    session.add(new_playlist)
    session.commit()
    session.refresh(new_playlist)
    return {"uuid": new_display.uuid, "message": "Display registered", "api_key": new_display.api_key}

@router.get('/admin/locations')
async def get_locations(session:Session = Depends(get_session)):
    locations = session.exec(select(col(Display.location)).distinct()).all()
    return {"locations": locations}

@router.get('/admin/display_by_location/{location}')
async def get_displays_by_location(location : str, session = Depends(get_session)):
    displays = session.exec(
        select(Display.uuid, Display.name, Display.api_key)
        .where(col(Display.location) == location)
    ).all()
    display_list = [{'uuid': d[0], 'name': d[1], 'api_key': d[2]} for d in displays]
    return {"displays": display_list}



# ---------------- Authentication --------------
@router.post('/token', response_model= Token)
async def login_for_access_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()] , session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password , user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},)
    
    access_token_expires = timedelta(minutes= ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( data={"sub" : user.username} , expires_delta=access_token_expires  )

    return {"access_token" : access_token , "token_type" : "bearer"}

# ---------------- Upload Media ----------------
@router.post("/admin/upload_media", response_model=List[UploadMediaResponse])
async def upload_media(
   # current_user: Annotated[User, Depends(get_current_user)],
    files: List[UploadFile] = File(...),
    display_uuids: Optional[List[UUID]] = Form(None),
    override_playlist: bool = Form(False),
    session: Session = Depends(get_session)
):
    responses = []

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # MODIFIED: TRACK PLAYLISTS THAT HAVE BEEN CLEARED FOR OVERRIDE
    cleared_playlists = set()

    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_content = await file.read()
        sha256_hash = hashlib.sha256(file_content).hexdigest()

        existing_media = session.exec(
            select(Media).where(Media.sha256_hash == sha256_hash)
        ).first()

        if existing_media:
            media = existing_media
            print(f"File with hash {sha256_hash} already exists as {media.id}. Skipping upload.")
        else:
            media_id = uuid4()
            filename = "".join(c for c in file.filename if c.isalnum() or c in "._-").rstrip()
            filepath_on_disk = os.path.join(STORAGE_PATH, f"{filename}")
            os.makedirs(STORAGE_PATH, exist_ok=True)
            try:
                with open(filepath_on_disk, "wb") as buffer:
                    buffer.write(file_content)
            except IOError as e:
                if os.path.exists(filepath_on_disk):
                    os.remove(filepath_on_disk)
                raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

            file_size = os.path.getsize(filepath_on_disk)
            media_type = "image" if file.content_type.startswith("image") else "video"

            media = Media(
                id=media_id,
                original_filename=file.filename,
                filepath_on_disk=filepath_on_disk,
                content_type=file.content_type,
                media_type=media_type,
                size=file_size,
                sha256_hash=sha256_hash
            )
            session.add(media)
            session.commit()
            session.refresh(media)

        assigned_uuids = []
        if display_uuids:
            for display_uuid in display_uuids:
                display_playlist = session.exec(
                    select(DisplayPlaylist).where(DisplayPlaylist.display_uuid == display_uuid)
                ).first()
                if not display_playlist:
                    continue

                # MODIFIED: ONLY CLEAR PLAYLIST ONCE PER DISPLAY WHEN OVERRIDE IS TRUE
                if override_playlist and display_uuid not in cleared_playlists:
                    session.exec(delete(PlaylistMediaLink).where(PlaylistMediaLink.display_playlist_id == display_playlist.id))
                    display_playlist.current_index = 0
                    display_playlist.last_updated = datetime.now()
                    session.add(display_playlist)
                    cleared_playlists.add(display_uuid)

                # Check if the media is already linked to this playlist
                existing_link = session.exec(
                    select(PlaylistMediaLink)
                    .where(PlaylistMediaLink.display_playlist_id == display_playlist.id)
                    .where(PlaylistMediaLink.media_id == media.id)
                ).first()

                # MODIFIED: IF LINK EXISTS AND IS NOT OVERRIDE, MARK AS NEW
                if existing_link and not override_playlist:
                    existing_link.is_new = True
                    session.add(existing_link)
                    assigned_uuids.append(display_uuid)
                    display_playlist.last_updated = datetime.now()
                    session.add(display_playlist)
                    continue

                last_item = session.exec(
                    select(PlaylistMediaLink)
                    .where(PlaylistMediaLink.display_playlist_id == display_playlist.id)
                    .order_by(PlaylistMediaLink.order.desc())
                ).first()
                next_order = last_item.order + 1 if last_item else 0

                playlist_link = PlaylistMediaLink(
                    display_playlist_id=display_playlist.id,
                    media_id=media.id,
                    order=next_order,
                    is_new=True,
                    # MODIFIED: SET THE OVERRIDE FLAG IN THE DATABASE
                    override=override_playlist
                )
                session.add(playlist_link)
                
                display_playlist.last_updated = datetime.now()
                session.add(display_playlist)
                assigned_uuids.append(display_uuid)
                
        session.commit()
        session.refresh(media)

        responses.append(UploadMediaResponse(
            message=f"Media '{file.filename}' uploaded to library",
            media_id=media.id,
            media_type=media.media_type,
            size=media.size,
            assigned_displays=assigned_uuids,
            # MODIFIED: RETURN THE OVERRIDE FLAG
            override=override_playlist
        ))
    
    return responses

@router.post("admin/media_to_delete", response_model= List[str])
async def media_to_delete():
    pass

# ---------------- Display Media Endpoints ----------------
# @router.get('/displays/{uuid}/media')
# async def get_display_media(current_user: Annotated[User, Depends(get_current_user)], uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
#     if display.uuid != uuid:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key for this display UUID")
#     display_playlist = session.exec(
#         select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == uuid)
#     ).first()
#     if not display_playlist:
#         raise HTTPException(status_code=404, detail=f"Playlist for display {uuid} not found.")
#     playlist_links = session.exec(
#         select(PlaylistMediaLink)
#         .where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id)
#         .order_by(PlaylistMediaLink.order)
#     ).all()
#     if not playlist_links:
#         raise HTTPException(status_code=404, detail=f"Playlist for display {uuid} is empty.")
#     current_index = display_playlist.current_index
#     if current_index >= len(playlist_links):
#         current_index = 0
#     media_link = playlist_links[current_index]
#     media_item = session.exec(select(Media).where(col(Media.id) == media_link.media_id)).first()
#     if not media_item or not os.path.exists(media_item.filepath_on_disk):
#         raise HTTPException(status_code=404, detail=f"Assigned media (ID: {media_link.media_id}) not found or file missing.")
#     display_playlist.current_index = (current_index + 1) % len(playlist_links)
#     session.add(display_playlist)
#     session.commit()
#     response = FileResponse(
#         media_item.filepath_on_disk,
#         media_type=media_item.content_type,
#     )
#     return response


@router.get('/displays/{uuid}/status')
async def get_display_status(current_user: Annotated[User, Depends(get_current_user)], uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key for this display UUID")
    display_playlist = session.exec(
        select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == uuid)
    ).first()
    if not display_playlist:
        return {"status": "no_playlist_assigned", "last_updated": None, "playlist_item_count": 0}
    playlist_links = session.exec(
        select(PlaylistMediaLink).where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id).order_by(PlaylistMediaLink.order)
    ).all()
    playlist_item_count = len(playlist_links)
    playlist_version_indicator = display_playlist.last_updated.isoformat() if display_playlist.last_updated else None
    return {
        "status": "active",
        "last_updated": playlist_version_indicator,
        "playlist_item_count": playlist_item_count
    }

# ---------------- Display Sync (NEW) ----------------
@router.get('/displays/{uuid}/sync')
async def display_sync(uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    """
    Returns all new media for a display.
    """
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key for this uuid")

    display_playlist = session.exec(
        select(DisplayPlaylist).where(DisplayPlaylist.display_uuid == uuid)
    ).first()

    if not display_playlist:
        return {
            "status": "no_playlist_assigned",
            "last_updated": None,
            "playlist_item_count": 0,
            "new_media": []
        }

    # MODIFIED: GET ALL LINKS THAT ARE MARKED AS NEW
    new_media_links = session.exec(
        select(PlaylistMediaLink).where(PlaylistMediaLink.display_playlist_id == display_playlist.id, PlaylistMediaLink.is_new == True).order_by(PlaylistMediaLink.order)
    ).all()

    # ADDED: GET ALL LINKS TO RETURN A CORRECT COUNT
    playlist_links = session.exec(
        select(PlaylistMediaLink).where(PlaylistMediaLink.display_playlist_id == display_playlist.id).order_by(PlaylistMediaLink.order)
    ).all()

    new_media = []
    for link in new_media_links:
        media_item = session.exec(select(Media).where(Media.id == link.media_id)).first()
        if media_item and os.path.exists(media_item.filepath_on_disk):
            new_media.append({
                "id": str(media_item.id),
                "url": f"/media/{media_item.id}",
                "type": media_item.media_type,
                "original_filename": media_item.original_filename,
                # MODIFIED: RETURN THE OVERRIDE FLAG FROM THE DATABASE
                "override": link.override
            })

    return {
        "status": "active",
        "last_updated": display_playlist.last_updated.isoformat() if display_playlist.last_updated else None,
        "playlist_item_count": len(playlist_links),
        "new_media": new_media
    }

# ---------------- Bulk Mark Downloaded ----------------
@router.post('/displays/{uuid}/mark_downloaded_bulk')
async def mark_downloaded_bulk(uuid: UUID, request_data: BulkMarkDownloadedRequest, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Invalid API Key for this display UUID")
    
    display_playlist = session.exec(select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) ==uuid)).first()
    if not display_playlist:
        raise HTTPException(status_code=404 , detail="Playlist not found for this display.")

    updated_count = 0
    for media_id in request_data.media_ids:
        playlist_link = session.exec(select(PlaylistMediaLink).where(col(PlaylistMediaLink.media_id) == media_id, PlaylistMediaLink.display_playlist_id == display_playlist.id)).first()
        if playlist_link:
            playlist_link.is_new = False
            # ADDED: RESET OVERRIDE FLAG AFTER DOWNLOAD
            playlist_link.override = False
            session.add(playlist_link)
            updated_count +=1

    session.commit()
    return {"message" : f"{updated_count} media items marked as downloaded"}

# ---------------- Get Specific Media ----------------
@router.get('/media/{media_id}')
async def get_specific_media(media_id: UUID, session: Session = Depends(get_session)):
    media_item = session.exec(select(Media).where(col(Media.id) == media_id)).first()
    if not media_item or not os.path.exists(media_item.filepath_on_disk):
        raise HTTPException(status_code=404, detail=f"Media ID {media_id} not found or file missing")

    return FileResponse(media_item.filepath_on_disk, media_type= media_item.content_type)