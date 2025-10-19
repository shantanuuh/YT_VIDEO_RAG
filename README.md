# 🎵 YouTube RAG Chat System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Streamlit web application that enables natural language conversations with YouTube videos using Retrieval-Augmented Generation (RAG). Users can interactively ask questions about a video and receive accurate, context-aware answers instantly. The system performs fully local processing using Ollama and Mistral LLM, with audio transcription via Whisper and semantic search with ChromaDB—no cloud APIs are required, ensuring privacy and offline functionality.

This project demonstrates practical expertise in speech-to-text transcription, semantic search, and LLM-based retrieval, making it a valuable tool for learning, research, content analysis, and as a portfolio showcase of advanced AI development skills.
---

## ✨ Key Features

- 🎬 **Interactive Web UI** - Beautiful Streamlit interface with real-time video processing
- 🔒 **100% Local** - Everything runs on your machine (privacy-first)
- 💬 **Context-Aware Chat** - Ask questions and get accurate answers from video content
- 📹 **Multi-Video Support** - Manage up to 5 videos simultaneously with isolated contexts
- ⚡ **Smart Processing** - Automatic audio format selection with fallback strategies
- 🎯 **Semantic Search** - ChromaDB vector database for intelligent information retrieval
- 📊 **Video Preview** - Rich metadata display with thumbnails and descriptions

---

## 🏗️ Architecture

```
YouTube URL → Audio Download (yt-dlp) → Transcription (Whisper) 
→ Text Chunking → Vector Embeddings (ChromaDB) → Semantic Search 
→ LLM Response (Ollama/Mistral) → Answer Display
```

**Tech Stack:**
- **Frontend:** Streamlit
- **Audio Processing:** yt-dlp, FFmpeg
- **Transcription:** OpenAI Whisper (base model)
- **Vector Store:** ChromaDB + Sentence Transformers
- **LLM:** Ollama with Mistral model

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg ([Download](https://ffmpeg.org/download.html))
- Ollama ([Install](https://ollama.ai))

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/youtube-rag-chat.git
cd youtube-rag-chat

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama and pull Mistral model
ollama serve
ollama pull mistral
```

### Run Application

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 💡 Usage

1. **Paste YouTube URL** in the sidebar
2. **Click "Process Video"** and wait for:
   - 📹 Video info extraction
   - 📥 Audio download
   - 📝 Transcription (longest step)
   - 📚 Vector index creation
3. **Start chatting** - Ask questions about the video content!

### Example Questions

```
"What are the main topics discussed?"
"Can you summarize the key points?"
"What did they say about [specific topic]?"
"What examples were given?"
```

---

## 📁 Project Structure

```
youtube-rag-chat/
│
├── app.py                 # Main Streamlit application
├── audio_processor.py     # YouTube download & audio extraction
├── transcription.py       # Whisper transcription service
├── vector_db.py          # ChromaDB vector store manager
├── local_llm.py          # Ollama LLM integration
├── config.py             # Configuration settings
├── requirements.txt      # Dependencies
│
└── data/                 # Auto-created
    ├── audio/           # Downloaded audio files
    ├── transcripts/     # Cached transcripts
    └── vector_db/       # ChromaDB storage
```

---

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Models
WHISPER_MODEL = "base"        # tiny, base, small, medium, large
OLLAMA_MODEL = "mistral"      # or llama2, codellama, etc.
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Processing
CHUNK_SIZE = 1000             # Text chunk size
CHUNK_OVERLAP = 100           # Overlap between chunks
MAX_VIDEO_LENGTH = 7200       # Max 2 hours

# LLM Settings
DEFAULT_MAX_TOKENS = 512      # Response length
DEFAULT_TEMPERATURE = 0.3     # Creativity (0.0-1.0)
```

---

## 📊 Performance

| Video Length | Processing Time | Memory Usage |
|--------------|----------------|--------------|
| 5 minutes    | ~50 seconds    | ~2GB         |
| 15 minutes   | ~2 minutes     | ~3GB         |
| 30 minutes   | ~4 minutes     | ~4GB         |
| 1 hour       | ~8 minutes     | ~6GB         |

*Tested on: Intel i7-10700K, 32GB RAM, RTX 3070*

**Notes:**
- GPU significantly speeds up transcription (~3x faster)
- Subsequent queries on same video are near-instant
- Transcripts are cached for re-use

---

## 🔧 Core Components

### 1. Audio Processor
- Extracts video metadata (title, duration, thumbnail)
- Downloads audio with multiple format fallbacks
- Validates YouTube URLs
- Handles region-restricted and age-gated videos

### 2. Transcription Service
- Uses OpenAI Whisper for speech-to-text
- Auto-detects GPU/CPU
- Caches transcripts to avoid re-processing
- Provides word count and segment timestamps

### 3. Vector Database
- Creates isolated collections per video
- Uses Sentence Transformers for embeddings
- Smart text chunking with overlap
- Semantic similarity search (top-3 results)

### 4. Local LLM
- Integrates with Ollama API
- Context-aware prompt engineering
- Health checking and model verification
- Configurable temperature and token limits

### 5. Streamlit UI
- Multi-video management (max 5)
- Real-time processing indicators
- Chat history with clearing
- System health monitoring

---

## 🐛 Troubleshooting

### Ollama Not Running
```bash
# Start Ollama server
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### Model Not Found
```bash
# Pull the required model
ollama pull mistral

# Check available models
ollama list
```

### FFmpeg Missing
```bash
# Windows (Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### CUDA Out of Memory
```python
# Use smaller Whisper model in config.py
WHISPER_MODEL = "tiny"  # or "base"
```

### Download Fails
- Check if video is region-restricted
- Try a different video URL
- Ensure stable internet connection
- Check yt-dlp is up to date: `pip install --upgrade yt-dlp`

---

## 🚀 Future Enhancements

- [ ] Playlist support (batch processing)
- [ ] Multi-language transcription
- [ ] Export chat history
- [ ] Video timestamp linking in responses
- [ ] Real-time live stream transcription
- [ ] Docker containerization
- [ ] REST API endpoints
- [ ] Custom LLM model support

---

## 📦 Dependencies

```
streamlit>=1.28.0
yt-dlp>=2023.11.16
openai-whisper>=20231117
chromadb>=0.4.15
sentence-transformers>=2.2.2
langchain>=0.0.346
torch>=2.0.0
requests>=2.31.0
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Shantanu Harkulkar**

- 📧 Email: shantanuhakulkar4@gmail.com
- 📍 Location: Mumbai, Maharashtra, India
- 💼 LinkedIn: [Shantanu Harkulkar](https://www.linkedin.com/in/shantanu-harkulkar-563b38269/)
- 🐙 GitHub: [@shantanuuh](https://github.com/shantanuuh))

---

## 🙏 Acknowledgments

- OpenAI for Whisper
- ChromaDB team for vector database
- Ollama for local LLM inference
- yt-dlp contributors

---

## 🏷️ Keywords

`rag` `llm` `streamlit` `youtube` `whisper` `chromadb` `mistral` `ollama` `nlp` `generative-ai` `semantic-search` `local-llm` `privacy-first` `speech-to-text`

---

<div align="center">

⭐ **Star this repo if you find it helpful!** ⭐

Made with ❤️ using Python, Streamlit & AI

</div>
