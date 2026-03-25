from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SpotifyTrack(BaseModel):
    ts: datetime
    ms_played: int
    master_metadata_track_name: Optional[str] = None
    master_metadata_album_artist_name: Optional[str] = None
    master_metadata_album_album_name: Optional[str] = None
    reason_end: Optional[str] = None
    shuffle: Optional[bool] = None
    skipped: Optional[bool] = None
    incognito_mode: Optional[bool] = None