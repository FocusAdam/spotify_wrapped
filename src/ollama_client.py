import os
import ollama
from loguru import logger
from typing import Generator, Optional

class OllamaClient:
    """Client for interacting with local Ollama instance."""
    
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3.5:cloud")
        self.client = ollama.Client(host=self.host)
        logger.info(f"Initialized OllamaClient with host: {self.host}, model: {self.model}")
    
    def check_connection(self) -> bool:
        """Check if Ollama is reachable and model is available."""
        try:
            models = self.client.list()
            available_models = [m.model for m in models.get("models", [])]
            if self.model not in available_models and not any(self.model in m for m in available_models):
                logger.warning(f"Model {self.model} not found. Available models: {available_models}")
                return True  # Still connected, model might be pulled on first use
            logger.info(f"Ollama connection successful. Model {self.model} is available.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    def generate(self, system_prompt: str, user_prompt: str, context: str = "") -> str:
        """Generate a response from Ollama."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Context (user's listening data):\n{context}\n\nUser's question: {user_prompt}"
                })
            else:
                messages.append({"role": "user", "content": user_prompt})
            
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            return response.get("message", {}).get("content", "Przepraszam, wystąpił błąd podczas generowania odpowiedzi.")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Nie udało się połączyć z Ollama: {str(e)}"
    
    def generate_stream(self, system_prompt: str, user_prompt: str, context: str = "") -> Generator[str, None, None]:
        """Stream a response from Ollama."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
            ]
            
            if context:
                messages.append({
                    "role": "user", 
                    "content": f"Context (user's listening data):\n{context}\n\nUser's question: {user_prompt}"
                })
            else:
                messages.append({"role": "user", "content": user_prompt})
            
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                    
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield f"Nie udało się połączyć z Ollama: {str(e)}"