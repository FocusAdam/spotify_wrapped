import json
from pathlib import Path
from pydantic import ValidationError
from loguru import logger
from models import SpotifyTrack

class SpotifyFileExtractor:
    def __init__(self, data_folder: str):
        self.data_folder = Path(data_folder)
        logger.info(f"Initialized extractor with data folder: {self.data_folder}")

    def extract(self) -> list[SpotifyTrack]:
        valid_tracks = []
        file_patterns = self.data_folder.glob("Streaming_History_Audio_*.json")
        logger.info(f"Found {len(list(file_patterns))} potential data files")

        for file_path in file_patterns:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Processing file: {file_path.name} with {len(data)} items")

                    for item in data:
                        #We don't use tracks without name and these which were listened less than 30 seconds
                        if not item.get("master_metadata_track_name") or item.get("ms_played", 0) < 30000:
                            continue

                        try:
                            track = SpotifyTrack(**item)
                            valid_tracks.append(track)
                        except ValidationError as e:
                            logger.warning(f"Validation error in item: {e}")
                            continue
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in file {file_path.name}: {e}")
            except Exception as e:
                logger.error(f"Error processing file {file_path.name}: {e}")

        logger.info(f"Extraction complete. Valid tracks: {len(valid_tracks)}")
        return valid_tracks
