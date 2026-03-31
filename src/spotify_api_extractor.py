from datetime import datetime
from typing import List, Optional
from loguru import logger
from spotipy import Spotify
from models import SpotifyTrack



class SpotifyAPIExtractor:
    
    def __init__(self, spotify_client: Spotify):
        self.spotify = spotify_client
        logger.info("SpotifyAPIExtractor initialized with authenticated client")
    
    def extract_recently_played(self, limit: int = 50) -> List[SpotifyTrack]:
        try:
            logger.info(f"Fetching {limit} recently played tracks...")
            
            # Fetch recently played from Spotify API
            results = self.spotify.current_user_recently_played(limit=limit)
            
            tracks = []
            for item in results.get('items', []):
                track_data = item.get('track', {})
                played_at = item.get('played_at')
                
                if not track_data:
                    continue

                track = self._convert_to_spotify_track(track_data, played_at)
                if track:
                    tracks.append(track)
            
            logger.info(f"Successfully extracted {len(tracks)} recently played tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch recently played tracks: {e}")
            raise
    
    def extract_top_tracks(
        self,
        time_range: str = 'medium_term',
        limit: int = 50
    ) -> List[SpotifyTrack]:
        try:
            logger.info(f"Fetching top tracks for time range: {time_range}")
            
            results = self.spotify.current_user_top_tracks(
                time_range=time_range,
                limit=limit
            )
            
            tracks = []
            for track_data in results.get('items', []):
                track = self._convert_to_spotify_track(track_data, played_at=None)
                if track:
                    tracks.append(track)
            
            logger.info(f"Successfully extracted {len(tracks)} top tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch top tracks: {e}")
            raise
    
    def extract_saved_tracks(self, limit: int = 50) -> List[SpotifyTrack]:
        try:
            logger.info(f"Fetching saved tracks...")
            
            results = self.spotify.current_user_saved_tracks(limit=limit)
            
            tracks = []
            for item in results.get('items', []):
                track_data = item.get('track', {})
                added_at = item.get('added_at')
                
                if not track_data:
                    continue
                
                # Use added_at as played_at for saved tracks
                track = self._convert_to_spotify_track(track_data, played_at=added_at)
                if track:
                    tracks.append(track)
            
            logger.info(f"Successfully extracted {len(tracks)} saved tracks")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch saved tracks: {e}")
            raise
    
    def extract_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[SpotifyTrack]:
        try:
            logger.info(f"Fetching tracks from playlist: {playlist_id}")
            
            results = self.spotify.playlist_tracks(playlist_id, limit=limit)
            
            tracks = []
            for item in results.get('items', []):
                track_data = item.get('track', {})
                added_at = item.get('added_at')
                
                if not track_data:
                    continue
                
                track = self._convert_to_spotify_track(track_data, played_at=added_at)
                if track:
                    tracks.append(track)
            
            logger.info(f"Successfully extracted {len(tracks)} tracks from playlist")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to fetch playlist tracks: {e}")
            raise
    
    def _convert_to_spotify_track(
        self,
        track_data: dict,
        played_at: Optional[str] = None
    ) -> Optional[SpotifyTrack]:
        try:
            # Extract track information
            track_name = track_data.get('name', '')
            
            # Get artist name (first artist)
            artists = track_data.get('artists', [])
            artist_name = artists[0].get('name', '') if artists else ''
            
            # Get album name
            album = track_data.get('album', {})
            album_name = album.get('name', '')
            
            # Get duration in milliseconds
            duration_ms = track_data.get('duration_ms', 0)
            
            # Get Spotify URIs
            spotify_track_uri = track_data.get('uri', '')
            spotify_album_uri = album.get('uri', '')
            spotify_artist_uri = artists[0].get('uri', '') if artists else ''
            
            # Parse played_at timestamp
            if played_at:
                try:
                    # Parse ISO format timestamp and keep as datetime object
                    ts_played = datetime.fromisoformat(played_at.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    ts_played = datetime.utcnow()
            else:
                # Use current time if no played_at provided
                ts_played = datetime.utcnow()
            
            # Create SpotifyTrack instance
            track = SpotifyTrack(
                ts=ts_played,
                platform="spotify_api",
                ms_played=duration_ms,
                conn_country="N/A",
                ip_addr="N/A",
                master_metadata_track_name=track_name,
                master_metadata_album_artist_name=artist_name,
                master_metadata_album_album_name=album_name,
                spotify_track_uri=spotify_track_uri,
                episode_name=None,
                episode_show_name=None,
                spotify_episode_uri=None,
                reason_start="api_fetch",
                reason_end="api_fetch",
                shuffle=False,
                skipped=False,
                offline=False,
                offline_timestamp=None,
                incognito_mode=False
            )
            
            return track
            
        except Exception as e:
            logger.warning(f"Failed to convert track data: {e}")
            return None
    
    def get_user_profile(self) -> dict:
        """
        Fetch current user's Spotify profile.
        
        Returns:
            dict: User profile information
        """
        try:
            profile = self.spotify.current_user()
            logger.info(f"Fetched profile for user: {profile.get('display_name')}")
            return profile
        except Exception as e:
            logger.error(f"Failed to fetch user profile: {e}")
            raise


def get_api_extractor(spotify_client: Spotify) -> SpotifyAPIExtractor:
    """
    Factory function to create SpotifyAPIExtractor instance.
    
    Args:
        spotify_client: Authenticated Spotify client
        
    Returns:
        SpotifyAPIExtractor: Configured extractor instance
    """
    return SpotifyAPIExtractor(spotify_client)