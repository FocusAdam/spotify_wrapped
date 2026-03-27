import streamlit as st
import pandas as pd
import plotly.express as px
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import psycopg2
from ollama_client import OllamaClient
from query_helper import QueryHelper

st.set_page_config(
    page_title="Spotify Insights AI",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🎵"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 38px; color: #1DB954; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #b3b3b3; }
    .chat-container {
        background-color: #1a1f2e;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f2e;
        border-radius: 5px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1DB954;
    }
    </style>
    """, unsafe_allow_html=True)

load_dotenv()

@st.cache_resource
def get_engine():
        host=os.getenv("DB_HOST", "192.168.8.130")
        database=os.getenv("POSTGRES_DB", "spotify_db")
        user=os.getenv("POSTGRES_USER", "postgres")
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
        port = os.getenv("DB_PORT", "5432")

        db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        return create_engine(db_url, pool_size=5, max_overflow=10)
    

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=60)
    st.title("Twoje Ustawienia")
    
    limit_artystow = st.slider("Pokazuj Top", 5, 20, 10)
    
    st.info("Tutaj możesz zarządzać swoim połączeniem z bazą i konfiguracją dashboardu.")
    st.write("---")
    st.caption("Pamiętaj, że dane pobierane są z Twojego kontenera Docker.")

st.title("🎵 Moje Spotify Wrapped AI")
st.markdown("Analiza Twojej historii słuchania z bazy Postgres.")

# Create tabs for different sections
tab1, tab2 = st.tabs(["Dashboard", "AI Chat"])

with tab1:
    st.write("##")
    try:
        engine = get_engine()
        query = f"""
            SELECT artist_name, COUNT(*) as play_count, SUM(ms_played) / 60000 as total_minutes
            FROM raw_spotify_history 
            GROUP BY artist_name 
            ORDER BY total_minutes DESC LIMIT {limit_artystow}
        """
        df = pd.read_sql_query(query, engine)
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Łączny czas", f"{int(df['total_minutes'].sum())} min")
            col2.metric("Top Artysta", df.iloc[0]['artist_name'])
            col3.metric("Liczba odtworzeń", f"{df['play_count'].sum()}")
            
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

with tab2:
    st.write("##")
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display all previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    user_prompt = st.chat_input("Np. 'W jakich godzinach najczęściej słucham muzyki?'...")
    if user_prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        try:
            engine = get_engine()
            query_helper = QueryHelper(engine=engine)
            ollama_client = OllamaClient()
            
            # Get comprehensive context about user's listening data
            context = query_helper.get_comprehensive_context()
            
            # System prompt for the AI
            system_prompt = """You are a helpful AI assistant analyzing Spotify listening history. 
You respond in Polish language. You have access to the user's Spotify listening data.
Analyze the provided data and give insightful, personalized responses about their music preferences.
Be friendly, conversational, and provide interesting insights based on the data.
If the user asks about something not in the data, politely explain that you can only analyze the listening history available in their database."""
            
            with st.spinner("Analizuję Twoje dane muzyczne..."):
                response = ollama_client.generate(system_prompt, user_prompt, context)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(response)
        except Exception as e:
            error_msg = f"Przepraszam, wystąpił błąd: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            with st.chat_message("assistant"):
                st.markdown(error_msg)
    st.write("##")
    