import streamlit as st
from audio_processor import AudioProcessor
from transcription import TranscriptionService
from vector_db import VectorDBManager
from local_llm import LocalLLM
from config import MAX_CHAT_HISTORY, OLLAMA_MODEL
import time

# Page configuration
st.set_page_config(
    page_title="YouTube RAG Chat",
    page_icon="🎵",
    layout="wide"
)

class YouTubeRAGChat:
    def __init__(self):
        self.audio_processor = AudioProcessor()
        self.transcription_service = TranscriptionService()
        self.vector_db = VectorDBManager()
        
        # Initialize LLM with health check
        self.llm = LocalLLM(model_name=OLLAMA_MODEL)
        
        # Initialize session state
        if 'processed_videos' not in st.session_state:
            st.session_state.processed_videos = []
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_video' not in st.session_state:
            st.session_state.current_video = None
        if 'processing' not in st.session_state:
            st.session_state.processing = False
        if 'llm_health_checked' not in st.session_state:
            st.session_state.llm_health_checked = False
        if 'video_info_cache' not in st.session_state:
            st.session_state.video_info_cache = {}
        if 'current_collection' not in st.session_state:
            st.session_state.current_collection = None

    def check_system_health(self):
        """Check system dependencies health"""
        if not st.session_state.llm_health_checked:
            with st.spinner("Checking system health..."):
                health = self.llm.check_health()
                
                if not health["server_accessible"]:
                    st.error("🔴 Ollama server is not running!")
                    st.markdown("""
                    **To fix this:**
                    1. Install Ollama: https://ollama.ai
                    2. Start the server: `ollama serve`
                    3. Refresh this page
                    """)
                    return False
                elif not health["model_available"]:
                    st.error(f"🔴 Model '{OLLAMA_MODEL}' not found!")
                    st.markdown(f"""
                    **To fix this:**
                    1. Pull the model: `ollama pull {OLLAMA_MODEL}`
                    2. Refresh this page
                    
                    **Available models:** {', '.join(health["available_models"]) if health["available_models"] else "None"}
                    """)
                    return False
                else:
                    st.success(f"✅ Ollama is ready with model: {OLLAMA_MODEL}")
                    st.session_state.llm_health_checked = True
                    return True
        return True

    def estimate_processing_time(self, duration_seconds):
        """Estimate processing time based on video duration"""
        if not duration_seconds:
            return "Unknown"
        
        # Rough estimates: download (1x) + transcription (0.5x) + processing (0.1x)
        total_seconds = duration_seconds * 1.6
        minutes = int(total_seconds / 60)
        
        if minutes == 0:
            return "Less than 1 minute"
        elif minutes == 1:
            return "About 1 minute"
        else:
            return f"About {minutes} minutes"

    def main_interface(self):
        """Main application interface"""
        st.title("🎵 YouTube RAG Chat")
        
        
        # System health check
        if not self.check_system_health():
            return
    
        # ---------------- Sidebar for video processing ----------------
        with st.sidebar:
            st.header("📹 Process Video")
            youtube_url = st.text_input("YouTube URL:", placeholder="Paste URL here...")
        
            if st.button("Process Video", use_container_width=True, disabled=st.session_state.processing):
                if youtube_url:
                    self.process_video(youtube_url)
                else:
                    st.error("Please enter a YouTube URL")
        
            # System status indicator
            st.markdown("---")
            st.markdown("**System Status:**")
            st.markdown(f"🟢 Ollama Model: `{OLLAMA_MODEL}`")
        
            # Show processed videos
            if st.session_state.processed_videos:
                st.header("📚 Your Videos")
                for video in st.session_state.processed_videos:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.info(f"📹 {video['title'][:30]}...")
                    with col2:
                        if st.button("Delete 🗑️", key=f"delete_{video['title']}"):
                            # Delete the vector collection
                            self.vector_db.delete_collection(video.get('collection_id'))
                            st.session_state.processed_videos.remove(video)
                            if st.session_state.current_video == video:
                                st.session_state.current_video = None
                                st.session_state.current_collection = None
                            st.rerun()
        
            # ---------------- Sidebar Video Preview ----------------
            if st.session_state.current_video:
                video = st.session_state.current_video
                st.markdown("---")
                st.subheader("🎬 Video Preview")
                
                # Safely get video info with fallbacks
                thumbnail_url = video.get("thumbnail_url", "")
                title = video.get("title", "Unknown Title")
                uploader = video.get("uploader", "Unknown Uploader")
                duration = video.get("duration", "Unknown Duration")
                view_count = video.get("view_count", 0)
                description = video.get("description", "No description available")
                duration_seconds = video.get("duration_seconds", 0)
                video_url = video.get("url", "")
                
                if thumbnail_url:
                    st.markdown(
                        f'<a href="{video_url}" target="_blank">'
                        f'<img src="{thumbnail_url}" style="width:100%; border-radius:10px; border:2px solid #00d4aa;">'
                        f'</a>',
                        unsafe_allow_html=True
                    )
                    st.markdown('<p style="text-align:center;">📸 Click thumbnail to view</p>', unsafe_allow_html=True)
                
                st.markdown(f"### {title}")
                st.markdown(f"**👤 Uploader:** {uploader}")
                st.markdown(f"**⏱️ Duration:** {duration}")
                
                if view_count:
                    st.markdown(f"**👀 Views:** {view_count:,}")
                
                estimate = self.estimate_processing_time(duration_seconds)
                st.info(f"⏳ Estimated processing time: {estimate}")
                
                with st.expander("📝 Video Description"):
                    st.write(description)
        
            # ---------------- Clear chat history button ----------------
            if st.session_state.chat_history:
                if st.button("🧹 Clear Chat History", use_container_width=True):
                    st.session_state.chat_history = []
                    st.rerun()
    
        # ---------------- Main chat area ----------------
        if st.session_state.current_video:
            self.display_chat_interface()
        else:
            self.display_welcome()

    def display_welcome(self):
        """Welcome screen when no video is selected"""
        st.markdown("""
        ## RAG-Based Conversational System for YouTube Video Analysis
        
        **How to use:**
        1. Paste a YouTube URL in the sidebar
        2. Click "Process Video" to download and transcribe
        3. Select a video from your library
        4. Start chatting with the video content!
        
        The app will:
        - Download audio from YouTube
        - Transcribe using Whisper AI  
        - Create a searchable knowledge base
        - Let you ask questions using Ollama's Mistral model
        
        **Note:** Each video is processed independently, and questions will only be answered based on the currently selected video's content.
        """)

    def display_chat_interface(self):
        """Display chat interface for current video"""
        video = st.session_state.current_video
        
        # Safely get video info with fallbacks
        title = video.get("title", "Unknown Video")
        uploader = video.get("uploader", "Unknown Uploader")
        word_count = video.get("word_count", 0)
        
        # Video info header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"External Knowledge Source: {title}")
        with col2:
            st.write(f"**By:** {uploader}")
            st.write(f"**Words:** {word_count}")
        
        st.markdown("---")
        
        # Display chat history
        for message in st.session_state.chat_history[-MAX_CHAT_HISTORY:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about this video..."):
            self.handle_user_message(prompt, title)

    def process_video(self, youtube_url):
        """Process YouTube video through the pipeline"""
        st.session_state.processing = True

        try:
            status_placeholder = st.empty()
            progress_bar = st.progress(0)

            # Step 1: Get video info
            status_placeholder.info("📹 Getting video information...")
            video_info = self.audio_processor.get_video_info(youtube_url)
            if not video_info['success']:
                status_placeholder.error(f"❌ {video_info['error']}")
                progress_bar.empty()
                return
            status_placeholder.success("✅ Video info retrieved!")
            progress_bar.progress(25)

            # Cache the full video info
            st.session_state.video_info_cache[youtube_url] = video_info

            # Step 2: Download audio
            status_placeholder.info("📥 Downloading audio...")
            audio_result = self.audio_processor.download_audio(youtube_url)
            if not audio_result['success']:
                status_placeholder.error(f"❌ Download failed: {audio_result['error']}")
                progress_bar.empty()
                return
            status_placeholder.success("✅ Audio downloaded!")
            progress_bar.progress(50)

            # Step 3: Transcribe
            status_placeholder.info("📝 Transcribing audio...")
            transcript_data = self.transcription_service.transcribe_audio(
                audio_result['audio_path'], video_info
            )
            if 'error' in transcript_data:
                status_placeholder.error(f"❌ Transcription failed: {transcript_data['error']}")
                progress_bar.empty()
                return
            status_placeholder.success("✅ Transcription completed!")
            progress_bar.progress(75)

            # Step 4: Add to vector DB and get collection name
            status_placeholder.info("📚 Creating search index...")
            collection_name = self.vector_db.add_transcript(transcript_data)
            if not collection_name:
                status_placeholder.error("❌ Failed to create search index")
                progress_bar.empty()
                return
            status_placeholder.success("✅ Search index created!")
            progress_bar.progress(100)

            # Update session state with COMPLETE video information
            processed_video = {
                'title': video_info.get('title', 'Unknown Title'),
                'uploader': video_info.get('uploader', 'Unknown Uploader'),
                'duration': video_info.get('duration', 'Unknown Duration'),
                'duration_seconds': video_info.get('duration_seconds', 0),
                'thumbnail_url': video_info.get('thumbnail_url', ''),
                'view_count': video_info.get('view_count', 0),
                'description': video_info.get('description', 'No description available'),
                'url': youtube_url,
                'word_count': transcript_data.get('word_count', 0),
                'collection_id': collection_name  # Store the collection ID
            }

            # Store current collection in session state
            st.session_state.current_collection = collection_name

            # Limit to 5 recent videos
            if len(st.session_state.processed_videos) >= 5:
                # Delete the vector DB collection for the oldest video
                oldest_video = st.session_state.processed_videos.pop(0)
                self.vector_db.delete_collection(oldest_video.get('collection_id'))

            st.session_state.processed_videos.append(processed_video)
            st.session_state.current_video = processed_video

            # Clear previous chat history when processing a new video
            st.session_state.chat_history = []

            status_placeholder.success("🎉 Video ready for chatting!")

        except Exception as e:
            status_placeholder.error(f"❌ Unexpected error: {str(e)}")

        finally:
            st.session_state.processing = False

    def handle_user_message(self, prompt, video_title):
        """Handle user message and generate response using current video's collection"""
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching video content and generating response..."):
                try:
                    # Search for relevant content in CURRENT collection only
                    search_results = self.vector_db.search(
                        prompt, 
                        collection_name=st.session_state.current_collection
                    )
                    
                    if search_results and search_results['documents']:
                        # Combine context from search results
                        context = "\n\n".join(search_results['documents'][0][:3])  # Use top 3 results
                        response = self.llm.generate_response(prompt, context)
                    else:
                        response = "I couldn't find relevant information in this video to answer your question."
                    
                    st.markdown(response)
                    
                except Exception as e:
                    response = f"Sorry, I encountered an error: {str(e)}"
                    st.markdown(response)
        
        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})

def main():
    app = YouTubeRAGChat()
    app.main_interface()

if __name__ == "__main__":
    main()