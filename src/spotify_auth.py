import os
from pathlib import Path
import streamlit as st
from spotipy import Spotify
from spotipy.oauth2 import SpotifyPKCE
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_SCOPES = [
    "user-read-recently-played",       # Recently played tracks
    "user-top-read",                   # Top artists and tracks
    "user-read-playback-state",        # Current playback state
    "user-library-read",               # Saved tracks and albums
    "playlist-read-private",           # Private playlists
    "playlist-read-collaborative",     # Collaborative playlists
]


class SpotifyAuthManager:
    
    def __init__(self):
        """Initialize the Spotify Auth Manager with credentials from environment."""
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8501/callback")
        
        if not self.client_id:
            raise ValueError(
                "SPOTIFY_CLIENT_ID not found in environment variables. "
                "Please add it to your .env file."
            )
        
        self.cache_path = Path(__file__).parent.parent / ".cache"
        
        logger.info(f"Initializing SpotifyAuthManager with redirect_uri: {self.redirect_uri}")
        logger.info(f"Token cache path: {self.cache_path}")
        
        self.auth_manager = SpotifyPKCE(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=" ".join(SPOTIFY_SCOPES),
            open_browser=False,
            cache_path=str(self.cache_path),
        )
        
        logger.info("SpotifyAuthManager initialized successfully")
    
    def get_auth_url(self) -> str:
        auth_url = self.auth_manager.get_authorize_url()
        logger.info("Generated Spotify authorization URL")
        return auth_url
    
    def get_access_token(self, code: str) -> dict:
        try:
            if not code or len(code) < 10:
                raise ValueError(
                    "Invalid authorization code format. "
                    "The code should be a long string (e.g., 'AQDx...'). "
                    "Please copy only the code part from the URL, not the full URL."
                )
            
            logger.info(f"Attempting to exchange code for tokens (code length: {len(code)})")
            
            token_info = self.auth_manager.get_access_token(code)
            
            if not token_info:
                raise ValueError(
                    "Failed to get access token. The code may have expired or been used already. "
                    "Please try the authorization process again."
                )
            
            logger.info("Successfully obtained access token")
            return token_info
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except Exception as e:
            error_msg = str(e).lower()
            logger.error(f"Full error details: {e}")
            
            if "invalid_grant" in error_msg or "invalid code" in error_msg:
                raise ValueError(
                    "The authorization code is invalid or has expired. "
                    "Please go back to step 1 and generate a new authorization code."
                )
            elif "redirect_uri" in error_msg or "redirect" in error_msg:
                raise ValueError(
                    f"Redirect URI mismatch. The redirect URI in your Spotify app settings "
                    f"must exactly match: {self.redirect_uri}. "
                    f"Please check your Spotify Developer Dashboard."
                )
            else:
                logger.error(f"Failed to get access token: {e}")
                raise ValueError(
                    f"Failed to exchange code for token: {str(e)}. "
                    f"Please try again or check the logs for more details."
                )
    
    def get_token_from_cache(self) -> dict:
        try:
            token_info = self.auth_manager.validate_token(
                self.auth_manager.cache_handler.get_cached_token()
            )
            if token_info:
                logger.info("Found valid token in cache")
                return token_info
            else:
                logger.info("No valid token found in cache")
                return None
        except Exception as e:
            logger.warning(f"Error reading token from cache: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        try:
            token_info = self.get_token_from_cache()
            return token_info is not None
        except Exception:
            return False
    
    def get_spotify_client(self, token_info: dict = None) -> Spotify:
        try:
            if token_info is None:
                token_info = self.get_token_from_cache()
            
            if not token_info:
                raise ValueError("No valid token available. Please complete OAuth flow first.")
            
            spotify = Spotify(auth=token_info['access_token'])
            logger.info("Created authenticated Spotify client")
            return spotify
        except Exception as e:
            logger.error(f"Failed to create Spotify client: {e}")
            raise
    
    def logout(self):
        try:
            if self.cache_path.exists():
                os.remove(self.cache_path)
                logger.info("Token cache cleared")
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")


@st.cache_resource
def get_auth_manager() -> SpotifyAuthManager:
    return SpotifyAuthManager()
