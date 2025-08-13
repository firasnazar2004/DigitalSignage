
from typing import Optional , List, Dict, Any
from uuid import UUID , uuid4 
from datetime import datetime 
from sqlmodel import Field, SQLModel, Relationship 
import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB

class Display(SQLModel, table = True): 
    uuid: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str 
    mac: str = Field(unique=True, index=True)
    location: str
    api_key: str = Field(default_factory=lambda: str(uuid4()))
    registered_at: datetime = Field(default_factory=datetime.now)

    playlist_link: Optional["DisplayPlaylist"] = Relationship(back_populates="display")


class Media(SQLModel , table = True): 
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    original_filename: str 
    filepath_on_disk : str 
    content_type: str 
    upload_timestamp: datetime = Field(default_factory=datetime.now)
    media_type : str
    size: int 
    sha256_hash : str = Field(unique=True,index= True)
   #configuration : Dict[str,Any] = Field(default_factory=dict, sa_column=sqlalchemy.Column(JSONB))
    playlist_media_links : List['PlaylistMediaLink'] = Relationship(back_populates='media')


    

class DisplayPlaylist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    display_uuid : UUID = Field(foreign_key="display.uuid" , unique=True)
    current_index: int = 0 
    last_updated: datetime = Field(default_factory=datetime.now)

    display: Display = Relationship(back_populates="playlist_link")
    playlist_media_links: List['PlaylistMediaLink'] = Relationship(back_populates="display_playlist")


class PlaylistMediaLink(SQLModel, table=True):
    display_playlist_id: Optional[int] = Field(default=None, foreign_key="displayplaylist.id", primary_key=True)
    media_id: Optional[UUID] = Field(default=None, foreign_key="media.id", primary_key=True)
    order: int = Field(default=0)
    is_new: bool = Field(default=True)

    display_playlist: DisplayPlaylist = Relationship(back_populates="playlist_media_links")
    media: Media = Relationship(back_populates="playlist_media_links")