import streamlit as st
import os
import time
from dotenv import load_dotenv
from dashboard_logic import create_database_engine, fetch_top_artists, create_top_artists_chart, prepare_top_tracks_data
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
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* CSS Variables for theming */
    :root {
        --spotify-green: #1DB954;
        --spotify-green-hover: #1ed760;
        --spotify-green-dark: #169c46;
        --bg-primary: #0e1117;
        --bg-secondary: #1a1f2e;
        --bg-tertiary: #252b3b;
        --text-primary: #ffffff;
        --text-secondary: #b3b3b3;
        --text-muted: #727272;
        --border-color: #2a2f3e;
        --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
        --shadow-glow: 0 0 20px rgba(29, 185, 84, 0.3);
        --transition-fast: 0.15s ease;
        --transition-normal: 0.3s ease;
        --transition-slow: 0.5s ease;
    }
    
    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, var(--bg-primary) 0%, #0a0d12 100%);
        color: var(--text-primary);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--spotify-green);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--spotify-green-hover);
    }
    
    /* Metric cards with hover effect */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        transition: all var(--transition-normal);
        box-shadow: var(--shadow-sm);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-lg);
        border-color: var(--spotify-green);
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 42px;
        color: var(--spotify-green);
        font-weight: 700;
        letter-spacing: -0.5px;
        animation: fadeInUp 0.6s ease;
    }
    
    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
        border-right: 1px solid var(--border-color);
    }
    
    section[data-testid="stSidebar"] .stSlider {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 16px;
    }
    
    /* Tab styling with animation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--bg-secondary);
        border-radius: 12px;
        padding: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 12px 24px;
        color: var(--text-secondary);
        font-weight: 500;
        transition: all var(--transition-normal);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--bg-tertiary);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--spotify-green) 0%, var(--spotify-green-dark) 100%);
        color: white;
        box-shadow: var(--shadow-md);
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, var(--spotify-green) 0%, var(--spotify-green-dark) 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 32px;
        font-weight: 600;
        transition: all var(--transition-normal);
        box-shadow: var(--shadow-sm);
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, var(--spotify-green-hover) 0%, var(--spotify-green) 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
    }
    
    .stButton button:active {
        transform: translateY(0);
    }
    
    /* Secondary button */
    .stButton button[kind="secondary"] {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
    }
    
    .stButton button[kind="secondary"]:hover {
        background: var(--bg-secondary);
        border-color: var(--spotify-green);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        animation: fadeIn 0.3s ease;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, var(--spotify-green-dark) 0%, var(--spotify-green) 100%);
        margin-left: 20%;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: var(--bg-secondary);
        margin-right: 20%;
    }
    
    /* Chat input */
    .stChatInputContainer {
        background: var(--bg-secondary);
        border-radius: 25px;
        border: 1px solid var(--border-color);
        padding: 8px;
    }
    
    .stChatInputContainer:focus-within {
        border-color: var(--spotify-green);
        box-shadow: var(--shadow-glow);
    }
    
    /* Data table styling */
    .stDataFrame {
        background: var(--bg-secondary);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .stDataFrame table {
        border-collapse: separate;
        border-spacing: 0;
    }
    
    .stDataFrame th {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-weight: 600;
        padding: 16px;
    }
    
    .stDataFrame td {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .stDataFrame tr:hover td {
        background: var(--bg-tertiary);
    }
    
    /* Info/Warning/Error boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        padding: 16px;
    }
    
    .stAlert[data-baseweb="notification"][kind="info"] {
        background: rgba(29, 185, 84, 0.1);
        border-left: 4px solid var(--spotify-green);
    }
    
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
    }
    
    .stAlert[data-baseweb="notification"][kind="error"] {
        background: rgba(244, 67, 54, 0.1);
        border-left: 4px solid #f44336;
    }
    
    .stAlert[data-baseweb="notification"][kind="success"] {
        background: rgba(29, 185, 84, 0.1);
        border-left: 4px solid var(--spotify-green);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--spotify-green) transparent transparent transparent;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-secondary);
        border-radius: 8px;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-tertiary);
        border-radius: 0 0 8px 8px;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Loading skeleton */
    .skeleton {
        background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--bg-tertiary) 50%, var(--bg-secondary) 75%);
        background-size: 200% 100%;
        animation: loading 1.5s infinite;
        border-radius: 8px;
    }
    
    @keyframes loading {
        0% { background-position: 200% 0; }
        100% { background-position: -200% 0; }
    }
    
    /* Plotly chart container */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Spotify login button special styling */
    .spotify-login-btn {
        background: linear-gradient(135deg, var(--spotify-green) 0%, var(--spotify-green-dark) 100%);
        color: white;
        padding: 16px 32px;
        border: none;
        border-radius: 25px;
        font-size: 18px;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 12px;
        transition: all var(--transition-normal);
        box-shadow: var(--shadow-md);
    }
    
    .spotify-login-btn:hover {
        background: linear-gradient(135deg, var(--spotify-green-hover) 0%, var(--spotify-green) 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-glow);
    }
    
    /* Footer styling */
    footer {
        visibility: hidden;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        div[data-testid="stMetricValue"] {
            font-size: 28px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 8px 16px;
            font-size: 14px;
        }
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
    # Logo and title with animation
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; animation: fadeIn 0.5s ease;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg" 
             width="80" 
             style="filter: drop-shadow(0 0 10px rgba(29, 185, 84, 0.5));">
        <h2 style="color: #1DB954; margin-top: 10px; font-weight: 600;">Spotify Insights</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("---")
    
    # Info box
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(29, 185, 84, 0.1) 0%, rgba(29, 185, 84, 0.05) 100%);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(29, 185, 84, 0.2);
        margin-top: 20px;
    ">
        <p style="color: #b3b3b3; font-size: 14px; margin: 0;">
            💡 <strong style="color: #1DB954;">Wskazówka:</strong> Dane pobierane są z Twojego kontenera Docker. Upewnij się, że baza danych jest uruchomiona.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 20px 0; color: #727272; font-size: 12px;">
        <p>Spotify Insights AI</p>
        <p>Wersja 1.0.0</p>
    </div>
    """, unsafe_allow_html=True)

# Main title (UI concern)
st.markdown("""
<div style="animation: fadeInUp 0.6s ease;">
    <h1 style="color: #ffffff; font-weight: 700; font-size: 2.5rem; margin-bottom: 0;">
        🎵 Moje Spotify Wrapped AI
    </h1>
    <p style="color: #b3b3b3; font-size: 1.1rem; margin-top: 8px;">
        Analiza Twojej historii słuchania z bazy Postgres
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Dashboard", "AI Chat", "Połącz ze Spotify"])

# Dashboard tab
with tab1:
    st.markdown("")
    
    # Slider for number of artists - moved from sidebar to dashboard
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("")
    with col2:
        limit_artystow = st.slider(
            "Liczba artystów",
            min_value=5,
            max_value=20,
            value=10,
            help="Wybierz ilu top artystów chcesz zobaczyć"
        )
    
    try:
        engine = get_engine()
        
        # Business logic calls - separated from UI
        df = fetch_top_artists(engine, limit_artystow)
        
        if not df.empty:
            # Section header with animation
            st.markdown("""
            <div style="animation: fadeInUp 0.4s ease; margin-bottom: 24px;">
                <h2 style="color: #ffffff; font-weight: 600; margin-bottom: 8px;">
                    📊 Twoje Statystyki
                </h2>
                <p style="color: #b3b3b3; font-size: 14px;">
                    Przegląd Twoich najpopularniejszych artystów
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display metrics with custom styling
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="text-align: center; animation: fadeInUp 0.5s ease;">
                    <div style="font-size: 24px; margin-bottom: 8px;">⏱️</div>
                </div>
                """, unsafe_allow_html=True)
                col1.metric("Łączny czas", f"{int(df['total_minutes'].sum())} min")
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center; animation: fadeInUp 0.6s ease;">
                    <div style="font-size: 24px; margin-bottom: 8px;">🎤</div>
                </div>
                """, unsafe_allow_html=True)
                col2.metric("Top Artysta", df.iloc[0]['artist_name'])
            
            with col3:
                st.markdown(f"""
                <div style="text-align: center; animation: fadeInUp 0.7s ease;">
                    <div style="font-size: 24px; margin-bottom: 8px;">🎵</div>
                </div>
                """, unsafe_allow_html=True)
                col3.metric("Liczba odtworzeń", f"{df['play_count'].sum()}")
            
            # Divider with animation
            st.markdown("""
            <div style="animation: fadeIn 0.8s ease; margin: 32px 0;">
                <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, #1DB954, transparent);">
            </div>
            """, unsafe_allow_html=True)
            
            # Display chart (UI concern)
            fig = create_top_artists_chart(df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 193, 7, 0.05) 100%);
                border-radius: 12px;
                padding: 24px;
                border: 1px solid rgba(255, 193, 7, 0.2);
                text-align: center;
                animation: fadeIn 0.5s ease;
            ">
                <div style="font-size: 48px; margin-bottom: 16px;">📭</div>
                <h3 style="color: #ffc107; margin-bottom: 8px;">Brak danych</h3>
                <p style="color: #b3b3b3; margin: 0;">
                    Baza danych jest pusta. Uruchom najpierw skrypt ETL (<code>main.py</code>)!
                </p>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
            border-radius: 12px;
            padding: 24px;
            border: 1px solid rgba(244, 67, 54, 0.2);
            text-align: center;
            animation: fadeIn 0.5s ease;
        ">
            <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
            <h3 style="color: #f44336; margin-bottom: 8px;">Błąd połączenia</h3>
            <p style="color: #b3b3b3; margin: 0;">
                Nie udało się połączyć z bazą danych: {str(e)}
            </p>
        </div>
        """, unsafe_allow_html=True)

# AI Chat tab
with tab2:
    st.markdown("")
    
    # Chat header with animation
    st.markdown("""
    <div style="animation: fadeInUp 0.4s ease; margin-bottom: 24px;">
        <h2 style="color: #ffffff; font-weight: 600; margin-bottom: 8px;">
            💬 Asystent AI
        </h2>
        <p style="color: #b3b3b3; font-size: 14px;">
            Zadaj pytanie o swoje dane muzyczne, a AI przeanalizuje je za Ciebie
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat history in session state (UI concern - Streamlit-specific)
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Chat container with styling
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message if no messages
        if len(st.session_state.messages) == 0:
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, rgba(29, 185, 84, 0.1) 0%, rgba(29, 185, 84, 0.05) 100%);
                border-radius: 16px;
                padding: 24px;
                border: 1px solid rgba(29, 185, 84, 0.2);
                text-align: center;
                animation: fadeIn 0.5s ease;
                margin-bottom: 24px;
            ">
                <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
                <h3 style="color: #1DB954; margin-bottom: 8px;">Cześć! Jestem Twoim asystentem muzycznym</h3>
                <p style="color: #b3b3b3; margin: 0;">
                    Możesz zadać mi pytania takie jak:<br>
                    • "W jakich godzinach najczęściej słucham muzyki?"<br>
                    • "Jaki jest mój ulubiony gatunek?"<br>
                    • "Który artysta jest najczęściej odtwarzany?"
                </p>
            </div>
            """, unsafe_allow_html=True)
        
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
    
    # Clear chat button
    if len(st.session_state.messages) > 0:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🗑️ Wyczyść historię czatu", use_container_width=True, type="secondary"):
                st.session_state.messages = []
                st.rerun()

# Spotify Connection tab (OAuth UI)
with tab3:
    st.markdown("")
    
    # Header with animation
    st.markdown("""
    <div style="animation: fadeInUp 0.4s ease; margin-bottom: 24px;">
        <h2 style="color: #ffffff; font-weight: 600; margin-bottom: 8px;">
            🎵 Połącz swoje konto Spotify
        </h2>
        <p style="color: #b3b3b3; font-size: 14px;">
            Zaloguj się do Spotify, aby pobrać dane bezpośrednio z Twojego konta
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Initialize auth manager
        auth_manager = get_auth_manager()
        
    
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
            
        
            st.write("---")
            
            # Top Tracks Visualization Section
            st.markdown("### Wizualizacja Top Utworów")
            st.markdown("Wybierz ile top utworów chcesz zobaczyć i z jakiego okresu.")
            
            # Initialize session state for visualization
            if 'viz_tracks' not in st.session_state:
                st.session_state.viz_tracks = None
                st.session_state.viz_num_tracks = 10
                st.session_state.viz_time_range = 'medium_term'
            
            # Slider for number of tracks
            col1, col2 = st.columns([2, 1])
            with col1:
                num_tracks = st.slider("Liczba utworów do wyświetlenia", min_value=5, max_value=50, value=10, step=5)
            with col2:
                time_range = st.selectbox(
                    "Okres czasu",
                    options=[
                        ('short_term', 'Ostatnie 4 tygodnie'),
                        ('medium_term', 'Ostatnie 6 miesięcy'),
                        ('long_term', 'Cały czas')
                    ],
                    format_func=lambda x: x[1],
                    index=1
                )[0]
            
            # Only fetch new data when button is clicked
            if st.button("🎵 Pokaż Top Utwory", use_container_width=True, type="primary"):
                with st.spinner(f"Pobieranie top {num_tracks} utworów..."):
                    tracks = api_extractor.extract_top_tracks(time_range=time_range, limit=num_tracks)
                    if tracks:
                        st.session_state.viz_tracks = tracks
                        st.session_state.viz_num_tracks = num_tracks
                        st.session_state.viz_time_range = time_range
                    else:
                        st.warning("Nie znaleziono utworów dla wybranego okresu.")
            
            # Display table from session state (persists across reruns)
            if st.session_state.viz_tracks:
                df_tracks = prepare_top_tracks_data(st.session_state.viz_tracks, st.session_state.viz_num_tracks)
                st.dataframe(
                    df_tracks,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", width="small"),
                        "Track": st.column_config.TextColumn("Utwór", width="large"),
                        "Artist": st.column_config.TextColumn("Artysta", width="medium")
                    }
                )
            
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
            
            # Display login button with enhanced styling
            st.markdown(f"""
            <div style="text-align: center; animation: fadeInUp 0.5s ease;">
                <a href="{auth_url}" target="_blank" style="text-decoration: none;">
                    <button class="spotify-login-btn" style="
                        background: linear-gradient(135deg, #1DB954 0%, #169c46 100%);
                        color: white;
                        padding: 18px 40px;
                        border: none;
                        border-radius: 30px;
                        font-size: 18px;
                        font-weight: 600;
                        cursor: pointer;
                        display: inline-flex;
                        align-items: center;
                        gap: 12px;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 15px rgba(29, 185, 84, 0.4);
                    ">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                            <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                        </svg>
                        Zaloguj się przez Spotify
                    </button>
                </a>
            </div>
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
  
    except Exception as e:
        st.error(f"❌ Wystąpił nieoczekiwany błąd: {str(e)}")
        logger.error(f"Error in Spotify connection tab: {e}")
    
    st.write("##")
