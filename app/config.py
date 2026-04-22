import os
from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "Arabic")
DEFAULT_QUESTION_COUNT = int(os.getenv("DEFAULT_QUESTION_COUNT", "6"))
DEFAULT_ROLE = os.getenv("DEFAULT_ROLE", "Backend Engineer")
DEFAULT_LEVEL = os.getenv("DEFAULT_LEVEL", "Mid-Level")
AGENT_NAME = os.getenv("AGENT_NAME", "interview-agent")

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))