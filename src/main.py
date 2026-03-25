import os
from pathlib import Path
from dotenv import load_dotenv
from extractors import SpotifyFileExtractor
from loaders import PostgresLoader

load_dotenv()

def main():
    current_file = Path(__file__).resolve()

    project_root = current_file.parent.parent
    data_dir = project_root /"data"/"inbox"
    data_dir.mkdir(parents=True, exist_ok=True)

    extractor = SpotifyFileExtractor(str(data_dir))
    tracks = extractor.extract()

    if tracks:
        loader = PostgresLoader()
        loader.load(tracks)

if __name__ == "__main__":
    main()