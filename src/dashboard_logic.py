import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def create_database_engine(host: str, database: str, user: str, password: str, port: str) -> Engine:

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    return create_engine(db_url, pool_size=5, max_overflow=10)


def fetch_top_artists(engine: Engine, limit: int = 10) -> pd.DataFrame:
    """
    Fetch top artists by listening time from the database.
    
    Args:
        engine: SQLAlchemy engine instance
        limit: Number of top artists to fetch
        
    Returns:
        DataFrame with columns: artist_name, play_count, total_minutes
        
    """
    query = """
        SELECT artist_name, COUNT(*) as play_count, SUM(ms_played) / 60000 as total_minutes
        FROM raw_spotify_history 
        GROUP BY artist_name 
        ORDER BY total_minutes DESC
        LIMIT :limit
    """
    return pd.read_sql_query(text(query), engine, params={"limit": limit})


def create_top_artists_chart(df: pd.DataFrame) -> px.bar:
    """
    Create a horizontal bar chart of top artists.
    
    Args:
        df: DataFrame with artist data (from fetch_top_artists)
        limit: Number displayed in chart title
        
    Returns:
        Plotly figure object

    """
    fig = px.bar(
        df, 
        x='total_minutes', 
        y='artist_name', 
        orientation='h',
        title=f"Top Artystów wg czasu słuchania",
        labels={'total_minutes': 'Minuty', 'artist_name': 'Artysta'},
        color='total_minutes',
        color_continuous_scale='Greens', 
        template="plotly_dark" 
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    return fig