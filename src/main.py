import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from extractors import SpotifyFileExtractor
from loaders import PostgresLoader

REQUIRED_ENV_VARS = [
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD"
]

def validate_environment():
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def main():
    load_dotenv()
    validate_environment()

    current_file = Path(__file__).resolve()

    project_root = current_file.parent.parent
    data_dir = project_root /"data"/"inbox"
    data_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Spotify data processing pipeline")
    logger.info(f"Data directory: {data_dir}")

    extractor = SpotifyFileExtractor(str(data_dir))
    tracks = extractor.extract()

    if tracks:
        logger.info(f"Extracted {len(tracks)} valid tracks")
        loader = PostgresLoader()
        loader.load(tracks)
        logger.info("Successfully loaded tracks into database")
    else:
        logger.warning("No valid tracks found for processing")

    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
