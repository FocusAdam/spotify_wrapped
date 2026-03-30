import threading
import http.server
import socketserver
import urllib.parse
from loguru import logger
from spotify_auth import get_auth_manager

class SpotifyCallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse the URL and query parameters
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Check if this is the callback endpoint
            if parsed_url.path == '/callback':
                # Get the authorization code
                code = query_params.get('code', [None])[0]
                
                if code:
                    logger.info(f"Received callback with authorization code (length: {len(code)})")
                    
                    try:
                        # Exchange code for tokens
                        auth_manager = get_auth_manager()
                        token_info = auth_manager.get_access_token(code)
                        
                        logger.info("Successfully exchanged code for tokens!")
                        
                        # Redirect back to Streamlit app
                        self.send_response(302)
                        self.send_header('Location', 'http://localhost:8501')
                        self.end_headers()
                        
                        # Also send a success page in case redirect doesn't work
                        success_html = """
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Spotify Auth Success</title>
                            <style>
                                body {
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    margin: 0;
                                    background: linear-gradient(135deg, #1DB954 0%, #191414 100%);
                                    color: white;
                                }
                                .container {
                                    text-align: center;
                                    padding: 40px;
                                    background: rgba(0,0,0,0.3);
                                    border-radius: 20px;
                                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                                }
                                h1 { margin-bottom: 20px; }
                                .success { font-size: 48px; margin-bottom: 20px; }
                                .message { font-size: 18px; margin-bottom: 30px; }
                                .link {
                                    color: #1DB954;
                                    text-decoration: none;
                                    font-size: 18px;
                                }
                                .link:hover { text-decoration: underline; }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="success">✅</div>
                                <h1>Autoryzacja zakończona!</h1>
                                <p class="message">Przekierowanie do aplikacji...</p>
                                <p><a href="http://localhost:8501" class="link">Kliknij tutaj, jeśli nie zostałeś przekierowany automatycznie</a></p>
                            </div>
                        </body>
                        </html>
                        """
                        self.wfile.write(success_html.encode())
                        
                    except Exception as e:
                        logger.error(f"Failed to exchange code for tokens: {e}")
                        
                        # Send error response
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        error_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Spotify Auth Error</title>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    display: flex;
                                    justify-content: center;
                                    align-items: center;
                                    height: 100vh;
                                    margin: 0;
                                    background: linear-gradient(135deg, #e74c3c 0%, #191414 100%);
                                    color: white;
                                }}
                                .container {{
                                    text-align: center;
                                    padding: 40px;
                                    background: rgba(0,0,0,0.3);
                                    border-radius: 20px;
                                    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                                }}
                                h1 {{ margin-bottom: 20px; }}
                                .error {{ font-size: 48px; margin-bottom: 20px; }}
                                .message {{ font-size: 18px; margin-bottom: 30px; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="error">❌</div>
                                <h1>Błąd autoryzacji</h1>
                                <p class="message">{str(e)}</p>
                                <p>Spróbuj ponownie w aplikacji.</p>
                            </div>
                        </body>
                        </html>
                        """
                        self.wfile.write(error_html.encode())
                else:
                    # No code in callback
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<h1>Error: No authorization code received</h1>')
            else:
                # Not the callback endpoint
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>404 Not Found</h1>')
                
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


class SpotifyCallbackServer:
    def __init__(self, host='127.0.0.1', port=8081):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the callback server in a background thread."""
        if self.server is not None:
            logger.warning("Callback server is already running")
            return
        
        try:
            # Create the server
            self.server = socketserver.TCPServer(
                (self.host, self.port),
                SpotifyCallbackHandler
            )
            
            # Start the server in a background thread
            self.server_thread = threading.Thread(
                target=self.server.serve_forever,
                daemon=True  # Daemon thread will be killed when main program exits
            )
            self.server_thread.start()
            
            logger.info(f"Spotify callback server started on http://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            raise
    
    def stop(self):
        """Stop the callback server."""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.server_thread = None
            logger.info("Spotify callback server stopped")
    
    def is_running(self):
        """Check if the server is running."""
        return self.server is not None and self.server_thread is not None and self.server_thread.is_alive()


# Global server instance
_callback_server = None


def start_callback_server(host='127.0.0.1', port=8081):
    """
    Start the global callback server.
    
    Args:
        host: Host to listen on
        port: Port to listen on
    """
    global _callback_server
    
    if _callback_server is None or not _callback_server.is_running():
        _callback_server = SpotifyCallbackServer(host, port)
        _callback_server.start()
    
    return _callback_server


def stop_callback_server():
    """Stop the global callback server."""
    global _callback_server
    
    if _callback_server is not None:
        _callback_server.stop()
        _callback_server = None


def get_callback_url(host='127.0.0.1', port=8081):
    """
    Get the callback URL for the server.
    
    Args:
        host: Host the server is listening on
        port: Port the server is listening on
        
    Returns:
        str: The callback URL
    """
    return f"http://{host}:{port}/callback"
