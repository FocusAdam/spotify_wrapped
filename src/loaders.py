import os
import psycopg2
from psycopg2.extras import execute_values
from loguru import logger
from models import SpotifyTrack
from tenacity import retry, stop_after_attempt, wait_exponential

class PostgresLoader:
    def __init__(self):
        self.conn_params = {
            "host": "localhost",
            "port": "5432",
            "database": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD")
        }
        logger.info(f"Initialized PostgresLoader with connection params: {self.conn_params}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def load(self, tracks: list[SpotifyTrack]):
        if not tracks:
            logger.info("No tracks to load")
            return

        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            cur = conn.cursor()

            insert_query = """
                INSERT INTO raw_spotify_history
                (played_at, ms_played, track_name, artist_name, album_name, reason_end, shuffle, skipped, incognito)
                VALUES %s
                ON CONFLICT (played_at, track_name) DO NOTHING;
            """

            values = [
                (
                    t.ts,
                    t.ms_played,
                    t.master_metadata_track_name,
                    t.master_metadata_album_artist_name,
                    t.master_metadata_album_album_name,
                    t.reason_end,
                    t.shuffle,
                    t.skipped,
                    t.incognito_mode
                )
                for t in tracks
            ]

            execute_values(cur, insert_query, values)
            conn.commit()
            logger.info(f"Successfully loaded {len(tracks)} tracks into database")
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection error: {e}")
            raise
        except psycopg2.IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during load: {e}")
            raise
        finally:
            if cur:
                cur.close()
                logger.debug("Cursor closed")
            if conn:
                conn.close()
                logger.debug("Connection closed")
