import streamlit as st
import os
import time
from dotenv import load_dotenv
from dashboard_logic import create_database_engine, fetch_top_artists, create_top_artists_chart
from chat_logic import get_ai_response
from spotify_auth import get_auth_manager
from spotify_api_extractor import get_api_extractor
from spotify_callback_server import start_callback_server, get_callback_url
from loaders import PostgresLoader
from loguru import logger

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

# Start the callback server on app load
@st.cache_resource
def start_callback():
    """Start the Spotify OAuth callback server."""
    try:
        callback_url = get_callback_url()
        start_callback_server()
        logger.info(f"Callback server started at {callback_url}")
        return callback_url
    except Exception as e:
        logger.error(f"Failed to start callback server: {e}")
        return None

# Initialize callback server
callback_url = start_callback()


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
tab1, tab2, tab3 = st.tabs(["Dashboard", "AI Chat", "Połącz ze Spotify"])

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

# Spotify Connection tab (OAuth UI)
with tab3:
    st.write("##")
    st.markdown("### 🎵 Połącz swoje konto Spotify")
    st.markdown("Zaloguj się do Spotify, aby pobrać dane bezpośrednio z Twojego konta.")
    
    try:
        # Initialize auth manager
        auth_manager = get_auth_manager()
        
        # Check if user is already authenticated
        if auth_manager.is_authenticated():
            st.success("✅ Jesteś zalogowany do Spotify!")
            
            # Get authenticated client from cache
            spotify_client = auth_manager.get_spotify_client()
            api_extractor = get_api_extractor(spotify_client)
            user_profile = api_extractor.get_user_profile()
            
            # Display user info
            col1, col2 = st.columns([1, 3])
            with col1:
                if user_profile.get('images'):
                    st.image(user_profile['images'][0]['url'], width=100)
                else:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=100)
            with col2:
                st.markdown(f"**{user_profile.get('display_name', 'Użytkownik')}**")
                st.markdown(f"📧 {user_profile.get('email', 'Brak email')}")
                st.markdown(f"👥 {user_profile.get('followers', {}).get('total', 0)} obserwujących")
            
            st.write("---")
            
            # Fetch data options
            st.markdown("### 📥 Pobierz dane z Spotify")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🕐 Ostatnio słuchane", use_container_width=True):
                    with st.spinner("Pobieranie ostatnio słuchanych utworów..."):
                        tracks = api_extractor.extract_recently_played(limit=50)
                        if tracks:
                            engine = get_engine()
                            loader = PostgresLoader()
                            loader.load(tracks)
                            st.success(f"✅ Pobrano {len(tracks)} utworów!")
                            st.rerun()
                        else:
                            st.warning("Nie znaleziono utworów.")
                
                if st.button("⭐ Top utwory (6 miesięcy)", use_container_width=True):
                    with st.spinner("Pobieranie top utworów..."):
                        tracks = api_extractor.extract_top_tracks(time_range='medium_term', limit=50)
                        if tracks:
                            engine = get_engine()
                            loader = PostgresLoader()
                            loader.load(tracks)
                            st.success(f"✅ Pobrano {len(tracks)} utworów!")
                            st.rerun()
                        else:
                            st.warning("Nie znaleziono utworów.")
            
            with col2:
                if st.button("❤️ Polubione utwory", use_container_width=True):
                    with st.spinner("Pobieranie polubionych utworów..."):
                        tracks = api_extractor.extract_saved_tracks(limit=50)
                        if tracks:
                            engine = get_engine()
                            loader = PostgresLoader()
                            loader.load(tracks)
                            st.success(f"✅ Pobrano {len(tracks)} utworów!")
                            st.rerun()
                        else:
                            st.warning("Nie znaleziono utworów.")
                
                if st.button("📊 Top utwory (wszystkie)", use_container_width=True):
                    with st.spinner("Pobieranie top utworów (all time)..."):
                        tracks = api_extractor.extract_top_tracks(time_range='long_term', limit=50)
                        if tracks:
                            engine = get_engine()
                            loader = PostgresLoader()
                            loader.load(tracks)
                            st.success(f"✅ Pobrano {len(tracks)} utworów!")
                            st.rerun()
                        else:
                            st.warning("Nie znaleziono utworów.")
            
            st.write("---")
            
            # Logout button
            if st.button("🚪 Wyloguj się", type="secondary"):
                auth_manager.logout()
                st.success("Wylogowano pomyślnie!")
                st.rerun()
        
        else:
            # Show login UI
            st.info("Nie jesteś zalogowany do Spotify. Kliknij poniższy przycisk, aby się zalogować.")
            
            # Generate auth URL with callback server URL
            
            callback_url = get_callback_url()
            auth_url = auth_manager.get_auth_url()
            
            # Display login button
            st.markdown(f"""
            <a href="{auth_url}" target="_blank">
                <button style="
                    background-color: #1DB954;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 25px;
                    font-size: 18px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                ">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                    </svg>
                    Zaloguj się przez Spotify
                </button>
            </a>
            """, unsafe_allow_html=True)
            
            st.write("---")
            
            # Instructions - automatic callback
            st.markdown(f"""
            ### 📋 Instrukcja:
            1. Kliknij przycisk "Zaloguj się przez Spotify" powyżej
            2. Zostaniesz przekierowany na stronę Spotify
            3. Zaloguj się i zatwierdź dostęp do Twoich danych
            4. Po autoryzacji, zostaniesz automatycznie przekierowany z powrotem
            5. Odśwież stronę, aby zobaczyć swoje dane
            
            **Callback URL:** `{callback_url}`
            
            ✅ **Automatyczne logowanie** - nie musisz kopiować kodu!
            """)
    
    except ValueError as e:
        st.error(f"❌ Błąd konfiguracji: {str(e)}")
        st.markdown("""
        ### ⚠️ Brak konfiguracji Spotify
        
        Aby używać tej funkcji, musisz skonfigurować zmienne środowiskowe:
        
        1. Przejdź na [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
        2. Utwórz nową aplikację
        3. Dodaj redirect URI: `http://127.0.0.1:8501/callback`
        4. Skopiuj Client ID do zmiennej `SPOTIFY_CLIENT_ID` w pliku `.env`
        
        Przykładowy plik `.env`:
        ```
        SPOTIFY_CLIENT_ID=your_client_id_here
        SPOTIFY_CLIENT_SECRET=your_client_secret_here
        SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501/callback
        ```
        """)
    except Exception as e:
        st.error(f"❌ Wystąpił nieoczekiwany błąd: {str(e)}")
        logger.error(f"Error in Spotify connection tab: {e}")
    
    st.write("##")
