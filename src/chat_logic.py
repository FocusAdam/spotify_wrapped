from sqlalchemy.engine import Engine
from query_helper import QueryHelper
from ollama_client import OllamaClient


CHAT_SYSTEM_PROMPT = """You are a helpful AI assistant analyzing Spotify listening history. 
You respond in Polish language. You have access to the user's Spotify listening data.
Analyze the provided data and give insightful, personalized responses about their music preferences.
Be friendly, conversational, and provide interesting insights based on the data.
If the user asks about something not in the data, politely explain that you can only analyze the listening history available in their database."""


def get_ai_response(user_prompt: str, engine: Engine) -> str:
    """
    Generate an AI response based on user's Spotify data.
    
    This function orchestrates two services:
    1. QueryHelper - fetches listening data context from database
    2. OllamaClient - generates AI response using that context
    
    Args:
        user_prompt: The user's question/message
        engine: SQLAlchemy engine for database queries
        
    Returns:
        AI-generated response string
        
    """
    query_helper = QueryHelper(engine=engine)
    ollama_client = OllamaClient()
    
    # Get comprehensive context about user's listening data
    context = query_helper.get_comprehensive_context()
    
    # Generate response using Ollama
    response = ollama_client.generate(CHAT_SYSTEM_PROMPT, user_prompt, context)
    
    return response