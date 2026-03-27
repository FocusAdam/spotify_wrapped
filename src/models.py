from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SpotifyTrack(BaseModel):
    ts: datetime
    ms_played: int
    platform: Optional[str] = None
    conn_country: Optional[str] = None
    ip_addr: Optional[str] = None
    master_metadata_track_name: Optional[str] = None
    master_metadata_album_artist_name: Optional[str] = None
    master_metadata_album_album_name: Optional[str] = None
    spotify_track_uri: Optional[str] = None
    episode_name: Optional[str] = None
    episode_show_name: Optional[str] = None
    spotify_episode_uri: Optional[str] = None
    audiobook_title: Optional[str] = None
    audiobook_uri: Optional[str] = None
    audiobook_chapter_uri: Optional[str] = None
    audiobook_chapter_title: Optional[str] = None
    reason_start: Optional[str] = None
    reason_end: Optional[str] = None
    shuffle: Optional[bool] = None
    skipped: Optional[bool] = None
    offline: Optional[bool] = None
    offline_timestamp: Optional[int] = None
    incognito_mode: Optional[bool] = None
