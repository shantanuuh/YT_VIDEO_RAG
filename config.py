import os
from pathlib import Path

# Path settings
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
VECTORDB_DIR = DATA_DIR / "vector_db"

# Create directories
for directory in [DATA_DIR, AUDIO_DIR, TRANSCRIPT_DIR, VECTORDB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Model settings
WHISPER_MODEL = "base"

# Ollama settings
OLLAMA_MODEL = "mistral"  # The model you pulled
OLLAMA_BASE_URL = "http://localhost:11434"  # Default Ollama server URL

# Embedding model (still using SentenceTransformers)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Processing settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
MAX_VIDEO_LENGTH = 7200  # 2 hours

# UI settings
MAX_CHAT_HISTORY = 20

# LLM Generation settings
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.3