import streamlit as st
import os
from dotenv import load_dotenv
from dashboard_logic import create_database_engine, fetch_top_artists, create_top_artists_chart
from chat_logic import get_ai_response

# Page configuration (UI concern)
st.set_page_config(
    page_title="Spotify Insights AI",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🎵"
)

# CSS styling (UI concern)
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
    """
    Create and cache the database engine.
    
    Why keep @st.cache_resource here? This is a Streamlit-specific caching
    mechanism that ensures the engine is created once and reused across
    reruns. The underlying logic (create_database_engine) is in dashboard_logic.py
    and can be used without Streamlit.
    """
    host = os.getenv("DB_HOST", "192.168.8.130")
    database = os.getenv("POSTGRES_DB", "spotify_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    port = os.getenv("DB_PORT", "5432")
    return create_database_engine(host, database, user, password, port)


# Sidebar (UI concern)
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=60)
    st.title("Twoje Ustawienia")
    
    limit_artystow = st.slider("Pokazuj Top", 5, 20, 10)
    
    st.info("Tutaj możesz zarządzać swoim połączeniem z bazą i konfiguracją dashboardu.")
    st.write("---")
    st.caption("Pamiętaj, że dane pobierane są z Twojego kontenera Docker.")

# Main title (UI concern)
st.title("🎵 Moje Spotify Wrapped AI")
st.markdown("Analiza Twojej historii słuchania z bazy Postgres.")

# Create tabs for different sections
tab1, tab2 = st.tabs(["Dashboard", "AI Chat"])

# Dashboard tab
with tab1:
    st.write("##")
    try:
        engine = get_engine()
        
        # Business logic calls - separated from UI
        df = fetch_top_artists(engine, limit_artystow)
        
        if not df.empty:
            # Display metrics (UI concern)
            col1, col2, col3 = st.columns(3)
            col1.metric("Łączny czas", f"{int(df['total_minutes'].sum())} min")
            col2.metric("Top Artysta", df.iloc[0]['artist_name'])
            col3.metric("Liczba odtworzeń", f"{df['play_count'].sum()}")
            
            # Display chart (UI concern)
            st.write("##") 
            fig = create_top_artists_chart(df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Baza danych jest pusta. Uruchom najpierw skrypt ETL (`main.py`)!")
    except Exception as e:
        st.error(f"Nie udało się połączyć z bazą danych: {e}")

# AI Chat tab
with tab2:
    st.write("##")
    
    # Initialize chat history in session state (UI concern - Streamlit-specific)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display all previous messages (UI concern)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input (UI concern)
    user_prompt = st.chat_input("Np. 'W jakich godzinach najczęściej słucham muzyki?'...")
    if user_prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_prompt)
        
        try:
            engine = get_engine()
            
            # Business logic call - separated from UI
            with st.spinner("Analizuję Twoje dane muzyczne..."):
                response = get_ai_response(user_prompt, engine)
                
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