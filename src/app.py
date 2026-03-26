import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import psycopg2

st.set_page_config(page_title="Spotify Insights AI", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 38px; color: #1DB954; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #b3b3b3; }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "spotify_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=60)
    st.title("Twoje Ustawienia")
    
    limit_artystow = st.slider("Pokazuj Top", 5, 20, 10)
    
    st.info("Tutaj możesz zarządzać swoim połączeniem z bazą i konfiguracją dashboardu.")
    st.write("---")
    st.caption("Pamiętaj, że dane pobierane są z Twojego kontenera Docker.")

st.title("Moje Spotify Wrapped AI")
st.markdown("Analiza Twojej historii słuchania z bazy Postgres.")



with st.container():
    st.write("##")
    user_prompt = st.chat_input("Np. 'W jakich godzinach najczęściej słucham muzyki?'...")
    if user_prompt:
        st.chat_message("user").write(user_prompt)
        st.chat_message("assistant").write("Analizuję Twoją bazę danych... (Tu wkrótce wejdzie AI)")
    st.write("##")

st.divider()

try:
    conn = get_connection()

    query = f"""
        SELECT artist_name, COUNT(*) as play_count, SUM(ms_played) / 60000 as total_minutes
        FROM raw_spotify_history 
        GROUP BY artist_name 
        ORDER BY total_minutes DESC LIMIT {limit_artystow}
    """
    df = pd.read_sql_query(query, conn)
    

    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Łączny czas", f"{int(df['total_minutes'].sum())} min")
        m2.metric("Top Artysta", df.iloc[0]['artist_name'])
        m3.metric("Liczba odtworzeń", f"{df['play_count'].sum()}")

        st.write("##") 
        fig = px.bar(
            df, 
            x='total_minutes', 
            y='artist_name', 
            orientation='h',
            title=f"Top {limit_artystow} Artystów wg czasu słuchania",
            labels={'total_minutes': 'Minuty', 'artist_name': 'Artysta'},
            color='total_minutes',
            color_continuous_scale='Greens', 
            template="plotly_dark" 
        )
        
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Baza danych jest pusta. Uruchom najpierw skrypt ETL (`main.py`)!")

except Exception as e:
    st.error(f"Nie udało się połączyć z bazą danych: {e}")