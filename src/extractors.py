import json
from pathlib import Path
from pydantic import ValidationError
from models import SpotifyTrack

class SpotifyFileExtractor:
    def __init__(self, data_folder: str):
        self.data_folder = Path(data_folder)

    def extract(self) -> list[SpotifyTrack]:
        valid_tracks = []
        file_patterns = self.data_folder.glob("Streaming_History_Audio_*.json")

        for file_path in file_patterns:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                for item in data:
                    #We don't use tracks without name and these which were listened less than 30 seconds
                    if not item.get("master_metadata_track_name") or item.get("ms_played", 0) < 30000:                                          
                        continue

                    try:
                        track = SpotifyTrack(**item)
                        valid_tracks.append(track)
                    except ValidationError:
                        continue

        return valid_tracks