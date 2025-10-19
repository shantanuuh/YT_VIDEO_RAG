import whisper
import json
from pathlib import Path
import torch
import streamlit as st
from config import TRANSCRIPT_DIR, WHISPER_MODEL

@st.cache_resource
def load_whisper_model(model_size=WHISPER_MODEL):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = whisper.load_model(model_size, device=device)
        return model
    except Exception as e:
        st.error(f"Error loading Whisper model: {e}")
        return None

class TranscriptionService:
    def __init__(self):
        self.model = load_whisper_model()
        self.transcripts_dir = Path(TRANSCRIPT_DIR)
    
    def transcribe_audio(self, audio_path, video_info):
        """Transcribe audio file and save transcript"""
        try:
            # Convert to Path object if it's a string
            audio_path = Path(audio_path) if isinstance(audio_path, str) else audio_path
            
            if not audio_path.exists():
                return {'error': f"Audio file not found: {audio_path}"}
            
            # Create safe filename
            safe_title = "".join(c for c in video_info['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:100]  # Limit length
            transcript_path = self.transcripts_dir / f"{safe_title}.json"
            
            # Use cached transcript if available
            if transcript_path.exists():
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            if not self.model:
                return {'error': 'Whisper model not loaded'}
            
            # Transcribe audio
            result = self.model.transcribe(str(audio_path))
            
            transcript_data = {
                'title': video_info['title'],
                'uploader': video_info['uploader'],
                'transcript': result['text'],
                'word_count': len(result['text'].split()),
                'segments': result.get('segments', [])
            }
            
            # Save transcript
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            return transcript_data
            
        except Exception as e:
            return {'error': f"Transcription error: {str(e)}"}