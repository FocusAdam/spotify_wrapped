import os
import pandas as pd
from sqlalchemy import create_engine, text
from loguru import logger
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class QueryHelper:
    """Helper class for querying Spotify listening data."""
    
    def __init__(self, engine=None):
        if engine:
            self.engine = engine
        else:
            host = os.getenv("DB_HOST", "192.168.8.130")
            database = os.getenv("POSTGRES_DB", "spotify_db")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD", "postgres")
            port = os.getenv("DB_PORT", "5432")
            
            db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(db_url, pool_size=5, max_overflow=10)
    
    def get_top_artists(self) -> str:
        """Get user's top artists by listening time."""
        query = """
            SELECT artist_name, 
                   COUNT(*) as play_count,
                   SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            GROUP BY artist_name 
            ORDER BY total_minutes DESC
        """
        try:
            df = pd.read_sql_query(text(query), self.engine)
            if df.empty:
                return "No listening data available."
            
            result = "Top Artists by Listening Time:\n"
            for _, row in df.iterrows():
                result += f"- {row['artist_name']}: {int(row['total_minutes'])} min ({int(row['play_count'])} plays)\n"
            return result
        except Exception as e:
            logger.error(f"Error getting top artists: {e}")
            return f"Error: {e}"
    
    def get_top_tracks(self) -> str:
        """Get user's top tracks by play count."""
        query = """
            SELECT track_name, artist_name,
                   COUNT(*) as play_count,
                   SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            WHERE track_name IS NOT NULL
            GROUP BY track_name, artist_name 
            ORDER BY total_minutes DESC
        """
        try:
            df = pd.read_sql_query(text(query), self.engine)
            if df.empty:
                return "No listening data available."
            
            result = "Top Tracks by Listening Time:\n"
            for _, row in df.iterrows():
                result += f"- {row['track_name']} by {row['artist_name']}: {int(row['total_minutes'])} min ({int(row['play_count'])} plays)\n"
            return result
        except Exception as e:
            logger.error(f"Error getting top tracks: {e}")
            return f"Error: {e}"
    
    def get_top_albums(self, limit: int = 15) -> str:
        """Get user's top albums by listening time."""
        query = """
            SELECT album_name, artist_name,
                   COUNT(*) as play_count,
                   SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            WHERE album_name IS NOT NULL
            GROUP BY album_name, artist_name 
            ORDER BY total_minutes DESC
            LIMIT :limit
        """
        try:
            df = pd.read_sql_query(text(query), self.engine, params={"limit": limit})
            if df.empty:
                return "No listening data available."
            
            result = "Top Albums by Listening Time:\n"
            for _, row in df.iterrows():
                result += f"- {row['album_name']} by {row['artist_name']}: {int(row['total_minutes'])} min\n"
            return result
        except Exception as e:
            logger.error(f"Error getting top albums: {e}")
            return f"Error: {e}"
    
    def get_listening_by_hour(self) -> str:
        """Analyze listening patterns by hour of day."""
        query = """
            SELECT EXTRACT(HOUR FROM played_at) as hour,
                   COUNT(*) as play_count,
                   SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            GROUP BY hour
            ORDER BY hour
        """
        try:
            df = pd.read_sql_query(text(query), self.engine)
            if df.empty:
                return "No listening data available."
            
            result = "Listening Patterns by Hour of Day:\n"
            max_hour = df.loc[df['total_minutes'].idxmax(), 'hour']
            min_hour = df.loc[df['total_minutes'].idxmin(), 'hour']
            
            for _, row in df.iterrows():
                hour = int(row['hour'])
                minutes = int(row['total_minutes'])
                result += f"- {hour:02d}:00 - {hour+1:02d}:00: {minutes} min\n"
            
            result += f"\nMost active hour: {int(max_hour)}:00\n"
            result += f"Least active hour: {int(min_hour)}:00\n"
            return result
        except Exception as e:
            logger.error(f"Error getting listening by hour: {e}")
            return f"Error: {e}"
    
    def get_listening_by_day(self) -> str:
        """Analyze listening patterns by day of week."""
        query = """
            SELECT EXTRACT(DOW FROM played_at) as day_of_week,
                   COUNT(*) as play_count,
                   SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            GROUP BY day_of_week
            ORDER BY day_of_week
        """
        try:
            df = pd.read_sql_query(text(query), self.engine)
            if df.empty:
                return "No listening data available."
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            result = "Listening Patterns by Day of Week:\n"
            
            for _, row in df.iterrows():
                day_idx = int(row['day_of_week'])
                day_name = days[day_idx]
                minutes = int(row['total_minutes'])
                result += f"- {day_name}: {minutes} min ({int(row['play_count'])} plays)\n"
            
            return result
        except Exception as e:
            logger.error(f"Error getting listening by day: {e}")
            return f"Error: {e}"
    
    def get_skip_rate(self) -> str:
        """Calculate skip rate statistics."""
        query = """
            SELECT 
                COUNT(*) as total_plays,
                SUM(CASE WHEN skipped = true THEN 1 ELSE 0 END) as skipped_plays,
                SUM(CASE WHEN shuffle = true THEN 1 ELSE 0 END) as shuffle_plays
            FROM raw_spotify_history
        """
        try:
            df = pd.read_sql_query(text(query), self.engine)
            if df.empty:
                return "No listening data available."
            
            row = df.iloc[0]
            total = int(row['total_plays'])
            skipped = int(row['skipped_plays'])
            shuffle = int(row['shuffle_plays'])
            
            skip_rate = (skipped / total * 100) if total > 0 else 0
            shuffle_rate = (shuffle / total * 100) if total > 0 else 0
            
            result = "Listening Behavior Statistics:\n"
            result += f"- Total Plays: {total}\n"
            result += f"- Skipped Plays: {skipped} ({skip_rate:.1f}%)\n"
            result += f"- Shuffle Plays: {shuffle} ({shuffle_rate:.1f}%)\n"
            return result
        except Exception as e:
            logger.error(f"Error getting skip rate: {e}")
            return f"Error: {e}"
    
    def get_comprehensive_context(self) -> str:
        """Get all available data as context for the AI."""
        context = "=== USER'S SPOTIFY LISTENING DATA ===\n\n"
        
        context += self.get_top_artists() + "\n"
        context += self.get_top_tracks() + "\n"
        context += self.get_listening_by_hour() + "\n"
        context += self.get_listening_by_day() + "\n"
        context += self.get_skip_rate() + "\n"
        
        return context