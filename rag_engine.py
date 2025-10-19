from llama_cpp import Llama
from config import LLM_MODEL_PATH
import streamlit as st

@st.cache_resource
def load_llm():
    """Load the local GGUF model"""
    return Llama(
        model_path=str(LLM_MODEL_PATH),
        n_ctx=4096,
        n_threads=4,
        verbose=False
    )

class LocalLLM:
    def __init__(self):
        self.llm = load_llm()
    
    def generate_response(self, query: str, context: str):
        """Generate response using local LLM with RAG context"""
        prompt = f"""Based on the following video transcript content, answer the user's question.

VIDEO CONTENT:
{context}

USER QUESTION: {query}

Answer based only on the video content. If the information isn't in the transcript, say so.

ANSWER: """
        
        try:
            response = self.llm(
                prompt,
                max_tokens=512,
                temperature=0.3,
                stop=["\n\n"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return f"Error: {str(e)}"