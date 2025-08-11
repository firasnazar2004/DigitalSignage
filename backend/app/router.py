from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends, status, Form
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from uuid import uuid4, UUID
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, col, delete
from fastapi.security import APIKeyHeader
from backend.app.models import Display, DisplayPlaylist, Media, PlaylistMediaLink
from backend.app.db import get_session  
from . import storage

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


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

class AssignMediaRequest(BaseModel):
    display__uuid: UUID
    media_ids: List[UUID]

class BulkMarkDownloadedRequest(BaseModel): 
    media_ids : List[UUID]
 

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_BASE_DIR = os.path.join(CURRENT_DIR, "storage")
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/svg+xml", "video/mp4", "video/webm", "video/ogg", "video/x-msvideo"}
STORAGE_PATH = os.path.join(STORAGE_BASE_DIR, "media")

router = APIRouter()



async def get_display_by_api_key(api_key: str = Depends(api_key_header), session: Session = Depends(get_session)):
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-API-KEY header missing")
    
    display = session.exec(select(Display).where(col(Display.api_key) == api_key)).first()
    if not display:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    
    return display



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
    new_display = Display(name= name   ,mac=mac, location=location)
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
    locations = session.exec( select(col(Display.location)).distinct() ).all()
    return {"locations": locations}


@router.get('/admin/display_by_location/{location}')
async def get_displays_by_location(location : str, session = Depends(get_session)):
    displays = session.exec(
        select(Display.uuid, Display.name, Display.api_key)
        .where(col(Display.location) == location)
    ).all()
    
    display_list = [{'uuid': d[0], 'name': d[1], 'api_key': d[2]} for d in displays]
    return {"displays": display_list}




@router.post("/admin/upload_media", response_model= List[UploadMediaResponse])
async def upload_media(
    #media_type: str,
    files: List[UploadFile] = File(...),
    display_uuids: Optional[List[UUID]] = Form(None), 
    session: Session = Depends(get_session)
):
    responses =[]
    for file in files: 
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    
    
        media_type = "image" if file.content_type.startswith("image") else "video"

        media_id = uuid4()
        extension = os.path.splitext(file.filename)[-1]
        filepath_on_disk = os.path.join(STORAGE_PATH, f"{media_id}{extension}")


        try:
            with open(filepath_on_disk, "wb") as buffer:
                while chunk := await file.read(8192):
                    buffer.write(chunk)
                    
        except IOError as e:
            #Delete partially written file if error arises
            if os.path.exists(filepath_on_disk):
                os.remove(filepath_on_disk)
            raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        

        file_size = os.path.getsize(filepath_on_disk)
        new_media = Media(
            id=media_id,
            original_filename=file.filename,
            filepath_on_disk=filepath_on_disk,
            content_type=file.content_type,
            media_type=media_type,
            size=file_size,
        )
        session.add(new_media)
        
        assigned_uuids = []
        if display_uuids:
            for display_uuid in display_uuids:
                display_playlist = session.exec(
                    select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == display_uuid)
                ).first()

                if not display_playlist:
                    continue

                last_item = session.exec(
                    select(PlaylistMediaLink)
                    .where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id)
                    .order_by(col(PlaylistMediaLink.order).desc())
                ).first()
                next_order = last_item.order + 1 if last_item else 0

                playlist_link = PlaylistMediaLink(
                    display_playlist_id=display_playlist.id,
                    media_id= new_media.id,
                    order = next_order,
                    is_new=True
                )

                
                session.add(playlist_link)

                
                display_playlist.last_updated = datetime.now()
                session.add(display_playlist)
                assigned_uuids.append(display_uuid)




        session.commit()
        session.refresh(new_media)

        

        responses.append(UploadMediaResponse(
            message=f"Media '{file.filename}' uploaded to library",
            media_id=new_media.id,
            media_type=new_media.media_type,
            size=new_media.size,
            assigned_displays=assigned_uuids
        ))

    return responses


@router.post("admin/media_to_delete", response_model= List[str])





@router.get('/displays/{uuid}/media')
async def get_display_media(uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key for this display UUID")
    display_playlist = session.exec(
        select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == uuid)
    ).first()
    if not display_playlist:
        raise HTTPException(status_code=404, detail=f"Playlist for display {uuid} not found.")
    playlist_links = session.exec(
        select(PlaylistMediaLink)
        .where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id)
        .order_by(PlaylistMediaLink.order)
    ).all()
    if not playlist_links:
        raise HTTPException(status_code=404, detail=f"Playlist for display {uuid} is empty.")
    current_index = display_playlist.current_index
    if current_index >= len(playlist_links):
        current_index = 0
    media_link = playlist_links[current_index]
    media_item = session.exec(select(Media).where(col(Media.id) == media_link.media_id)).first()
    if not media_item or not os.path.exists(media_item.filepath_on_disk):
        raise HTTPException(status_code=404, detail=f"Assigned media (ID: {media_link.media_id}) not found or file missing.")
    display_playlist.current_index = (current_index + 1) % len(playlist_links)
    session.add(display_playlist)
    session.commit()
    response = FileResponse(
        media_item.filepath_on_disk,
        media_type=media_item.content_type,
        #headers={"X-Media-Type": media_item.media_type, "X-Media-Configuration": json.dumps(media_item.configuration)}
    )
    return response


@router.get('/displays/{uuid}/status')
async def get_display_status(uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
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

@router.get('/displays/{uuid}/sync')
async def display_sync(uuid:UUID , session:Session = Depends(get_session) , display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail ="Invalid API key for this uuid")
    
    display_playlist = session.exec(select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid)==uuid)).first()

    if not display_playlist: 
        return {
            "status": "no_play_list_assigned",
            "last_updated": None , 
            "playlist_item_count" : 0, 
            "new_media" : []
        }
    
    playlist_links = session.exec(select(PlaylistMediaLink).where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id).order_by(PlaylistMediaLink.order) ).all()

    playlist_item_count = len(playlist_links)
    playlist_version_indicator = display_playlist.last_updated.isoformat() if display_playlist.last_updated else None

    new_media_links = session.exec(select(PlaylistMediaLink).where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id , col(PlaylistMediaLink.is_new) == True).order_by(PlaylistMediaLink.order)).all()

    new_media = []
    for link in new_media_links:
        media_item = session.exec(select(Media).where(col(Media.id) == link.media_id)).first()
        if media_item and os.path.exists(media_item.filepath_on_disk): 
            new_media.append({
                "id": str(media_item.id),
                "url" : f"/media/{media_item.id}", 
                "type" : media_item.media_type , 

            })

    return { 
        "status" : "active", 
        "last_updated" : playlist_version_indicator, 
        "playlist_item_count" : playlist_item_count, 
        "new_media" : new_media
    }


@router.post('/displays/{uuid}/mark_downloaded_bulk')
async def mark_downloaded_bulk(uuid: UUID, request_data: BulkMarkDownloadedRequest, session: Session = Depends(get_session) , display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail = "Invalid API Key for this display UUID")
    
    display_playlist = session.exec(select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) ==uuid)).first()

    if not display_playlist: 
        raise HTTPException(status_code=404 , detail="Playlist not found for this display.")
    
    updated_count = 0 
    for media_id in request_data.media_ids: 
        playlist_link = session.exec(select(PlaylistMediaLink).where(col(PlaylistMediaLink.media_id) == media_id, col(PlaylistMediaLink.display_playlist_id == display_playlist.id))).first()

        if playlist_link: 
            playlist_link.is_new = False
            session.add(playlist_link)
            updated_count +=1 
    
    session.commit()
    return {"message" : f"{updated_count} media items marked as downloaded"}

@router.get('/displays/{uuid}/media_to_download')
async def get_new_media_for_download(uuid: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid: 
        raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail='Invalid API Key for this display UUID')
    
    display_playlist = session.exec(
        select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid)==uuid)
    ).first()

    if not display_playlist:
        return []
    
    new_media_links = session.exec(
        select(PlaylistMediaLink).where(col(PlaylistMediaLink.display_playlist_id) == display_playlist.id , col(PlaylistMediaLink.is_new) == True).order_by(PlaylistMediaLink.order)
    ).all()

    new_media_ids = [link.media_id for link in new_media_links]
    return new_media_ids

@router.post('/displays/{uuid}/mark_downloaded/{media_id}')
async def mark_media_downloaded(uuid: UUID, media_id: UUID, session: Session = Depends(get_session), display: Display = Depends(get_display_by_api_key)):
    if display.uuid != uuid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API Key for this display UUID')

    # First, find the display's playlist
    display_playlist = session.exec(
        select(DisplayPlaylist).where(col(DisplayPlaylist.display_uuid) == uuid)
    ).first()

    if not display_playlist:
        raise HTTPException(status_code=404, detail="Playlist not found for this display.")
    
    # Now, find the specific playlist link using the media_id and the correct playlist id
    playlist_link = session.exec(
        select(PlaylistMediaLink)
        .where(
            col(PlaylistMediaLink.media_id) == media_id,
            col(PlaylistMediaLink.display_playlist_id) == display_playlist.id
        )
    ).first()

    if not playlist_link:
        raise HTTPException(status_code=404, detail="Media not found in this display's playlist.")

    playlist_link.is_new = False
    session.add(playlist_link)
    # The redundant session.add() is removed
    session.commit()
    session.refresh(playlist_link)

    return {"message": f"Media {media_id} marked as downloaded."}

@router.get('/media/{media_id}')
async def get_specific_media(media_id: UUID, session: Session = Depends(get_session)):
    media_item = session.exec(select(Media).where(col(Media.id) == media_id)).first()
    if not media_item or not os.path.exists(media_item.filepath_on_disk):
        raise HTTPException(status_code=404, detail=f"Media ID {media_id} not found or file missing")
    
    return FileResponse(
        media_item.filepath_on_disk,
        media_type= media_item.content_type
    )