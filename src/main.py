from loguru import logger
from etl_pipeline import run_spotify_etl

def main():
    """Entry point for running the Spotify ETL pipeline."""
    logger.info("Starting Spotify ETL pipeline from main.py")
    
    try:
        tracks_processed = run_spotify_etl()
        logger.info(f"Pipeline completed successfully. Processed {tracks_processed} tracks.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
