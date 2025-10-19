import requests
import json
import streamlit as st
from typing import Optional

class LocalLLM:
    def __init__(self, model_name: str = "mistral", base_url: str = "http://localhost:11434"):
        """Initialize Ollama client
        
        Args:
            model_name: Name of the Ollama model (e.g., 'mistral', 'llama2')
            base_url: Ollama server URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.generate_url = f"{base_url}/api/generate"
        
        # Test connection and model availability
        if not self._test_connection():
            st.error(f"⚠️ Cannot connect to Ollama server at {base_url}")
            st.info("Make sure Ollama is running: `ollama serve`")
        elif not self._check_model():
            st.error(f"⚠️ Model '{model_name}' not found")
            st.info(f"Pull the model first: `ollama pull {model_name}`")
    
    def _test_connection(self) -> bool:
        """Test if Ollama server is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def _check_model(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model.get("name", "").startswith(self.model_name) for model in models)
            return False
        except requests.exceptions.RequestException:
            return False
    
    def generate_response(self, query: str, context: str, max_tokens: int = 512, temperature: float = 0.3) -> str:
        """Generate response using Ollama with RAG context"""
        
        prompt = f"""Based on the following video transcript content, answer the user's question accurately and concisely.

VIDEO TRANSCRIPT:
{context}

USER QUESTION: {query}

Instructions:
- Answer based only on the information provided in the video transcript
- If the information isn't available in the transcript, clearly state that
- Be specific and cite relevant parts when possible
- Keep your response focused and helpful

ANSWER:"""
        
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9,
                    "stop": ["\n\nUSER:", "USER QUESTION:", "VIDEO TRANSCRIPT:"]
                }
            }
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=60  # Increased timeout for longer responses
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "").strip()
                
                # Clean up the response
                if generated_text:
                    # Remove any remaining prompt artifacts
                    generated_text = generated_text.replace("ANSWER:", "").strip()
                    return generated_text
                else:
                    return "I couldn't generate a response. Please try again."
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                try:
                    error_detail = response.json().get("error", "")
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                return f"Error: {error_msg}"
                
        except requests.exceptions.Timeout:
            return "Error: Request timed out. The model might be processing a complex query."
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama server. Make sure it's running with `ollama serve`."
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_available_models(self) -> list:
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model.get("name", "") for model in models]
            return []
        except requests.exceptions.RequestException:
            return []
    
    def check_health(self) -> dict:
        """Check Ollama server health and model availability"""
        health_status = {
            "server_accessible": False,
            "model_available": False,
            "available_models": []
        }
        
        # Check server
        health_status["server_accessible"] = self._test_connection()
        
        if health_status["server_accessible"]:
            # Check available models
            health_status["available_models"] = self.get_available_models()
            health_status["model_available"] = self._check_model()
        
        return health_status