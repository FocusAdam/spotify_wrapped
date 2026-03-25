import os
import psycopg2
from psycopg2.extras import execute_values
from models import SpotifyTrack

class PostgresLoader:
    def __init__(self):
        self.conn_params = {
            "host": "localhost",
            "port": "5432",
            "database": os.getenv("POSTGRES_DB"),
            "user": os.getenv("POSTGRES_USER"),
            "password": os.getenv("POSTGRES_PASSWORD")
        }

    def load(self, tracks: list[SpotifyTrack]):
        if not tracks:
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
        except Exception:
            pass
        finally:
            if cur: cur.close()
            if conn: conn.close()