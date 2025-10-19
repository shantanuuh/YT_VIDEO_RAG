import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import streamlit as st
from config import VECTORDB_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL

@st.cache_resource
def load_embedding_model():
    try:
        return SentenceTransformer(EMBEDDING_MODEL)
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

class VectorDBManager:
    def __init__(self):
        self.embedding_model = load_embedding_model()
        self.client = chromadb.PersistentClient(path=str(VECTORDB_DIR))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        self.current_collection = None
    
    def add_transcript(self, transcript_data):
        """Add transcript to vector database and return collection name"""
        try:
            if not self.embedding_model:
                return None
                
            # Use video title as collection name (sanitized)
            safe_title = "".join(c for c in transcript_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            collection_name = f"video_{hash(safe_title) % 1000000}"
            
            # Delete existing collection with same name to ensure clean state
            try:
                self.client.delete_collection(collection_name)
            except:
                pass  # Collection doesn't exist, which is fine
            
            collection = self.client.get_or_create_collection(collection_name)
            
            # Split transcript
            text = transcript_data['transcript']
            if not text.strip():
                return None
                
            chunks = self.text_splitter.split_text(text)
            
            # Add chunks to collection
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) > 10:  # Only add meaningful chunks
                    documents.append(chunk)
                    metadatas.append({
                        'video_title': transcript_data['title'],
                        'chunk_index': i,
                        'uploader': transcript_data.get('uploader', 'Unknown')
                    })
                    ids.append(f"chunk_{i}")
            
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                self.current_collection = collection_name
                return collection_name
            return None
            
        except Exception as e:
            st.error(f"Vector DB error: {e}")
            return None
    
    def search(self, query, collection_name=None, n_results=3):
        """Search in specific collection or current collection"""
        try:
            # If no collection specified, use current collection
            if collection_name is None:
                collection_name = self.current_collection
            
            if not collection_name:
                return None
            
            # Get the specific collection
            collection = self.client.get_collection(collection_name)
            
            # Search only in the specified collection
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            
            return results if results['documents'] else None
            
        except Exception as e:
            st.error(f"Search error: {e}")
            return None
    
    def delete_collection(self, collection_name):
        """Delete a specific collection"""
        try:
            self.client.delete_collection(collection_name)
            if self.current_collection == collection_name:
                self.current_collection = None
            return True
        except:
            return False
    
    def cleanup_all_collections(self):
        """Clean up all collections - use with caution"""
        try:
            collections = self.client.list_collections()
            for collection in collections:
                self.client.delete_collection(collection.name)
            self.current_collection = None
            return True
        except Exception as e:
            st.error(f"Cleanup error: {e}")
            return False