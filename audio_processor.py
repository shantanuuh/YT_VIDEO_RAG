import yt_dlp
import os
from pathlib import Path
import re
from urllib.parse import urlparse
from config import AUDIO_DIR, MAX_VIDEO_LENGTH
import streamlit as st

class AudioProcessor:
    def __init__(self, output_dir=AUDIO_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def sanitize_filename(self, title):
        """Remove invalid characters from filename"""
        return re.sub(r'[<>:"/\\|?*]', '', title)[:100]
    
    def validate_youtube_url(self, url):
        """Validate YouTube URL"""
        patterns = [
            r'^https?://(www\.)?youtube\.com/watch\?v=([^&]+)',
            r'^https?://youtu\.be/([^?]+)',
            r'^https?://(www\.)?youtube\.com/embed/([^/]+)'
        ]
        return any(re.match(pattern, url) for pattern in patterns)
    
    def get_available_formats(self, youtube_url):
        """Get available formats for a YouTube video"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'listformats': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return info.get('formats', [])
        except Exception as e:
            print(f"❌ Error getting formats: {e}")
            return []
    
    def get_best_audio_format(self, formats):
        """Select the best available audio format"""
        audio_formats = []
        
        for fmt in formats:
            # Look for audio-only formats
            if fmt.get('vcodec') == 'none' and fmt.get('acodec') != 'none':
                audio_formats.append(fmt)
        
        # Sort by quality (bitrate)
        audio_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
        
        if audio_formats:
            return audio_formats[0]['format_id']
        
        # If no audio-only formats, look for formats with audio
        for fmt in formats:
            if fmt.get('acodec') != 'none':
                return fmt['format_id']
        
        return None
    
    def get_video_info(self, youtube_url):
        """Extract video information without downloading"""
        if not self.validate_youtube_url(youtube_url):
            return {'success': False, 'error': 'Invalid YouTube URL'}
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Check video duration
                duration = info.get('duration', 0)
                if duration > MAX_VIDEO_LENGTH:
                    return {
                        'success': False, 
                        'error': f'Video too long ({self.format_duration(duration)}). Max allowed: {self.format_duration(MAX_VIDEO_LENGTH)}'
                    }
                
                # Get the best thumbnail
                thumbnail_url = self.get_best_thumbnail(info)
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown Title'),
                    'uploader': info.get('uploader', 'Unknown Uploader'),
                    'duration': self.format_duration(duration),
                    'duration_seconds': duration,
                    'thumbnail_url': thumbnail_url,
                    'view_count': info.get('view_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'description': self.truncate_description(info.get('description', '')),
                    'video_id': info.get('id', ''),
                    'url': youtube_url
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_best_thumbnail(self, info):
        """Get the best available thumbnail"""
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = None
        
        if thumbnails:
            for quality in ['maxresdefault', 'sddefault', 'hqdefault', 'mqdefault', 'default']:
                for thumb in thumbnails:
                    if thumb.get('id') == quality:
                        return thumb['url']
        
        # Fallback to standard YouTube thumbnail URL
        video_id = info.get('id')
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        return None
    
    def truncate_description(self, description, max_length=200):
        """Truncate description with ellipsis"""
        if not description:
            return "No description available"
        if len(description) <= max_length:
            return description
        return description[:max_length] + '...'
    
    def format_duration(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def download_audio(self, youtube_url):
        """Download audio from YouTube video with format fallbacks"""
        try:
            safe_filename = self.sanitize_filename("temp_audio")
            
            # Try multiple format strategies
            format_strategies = [
                'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
                'bestaudio/best',
                'best[height<=720]',  # Fallback to video with audio extraction
                'worstaudio/worst'    # Last resort: any audio format
            ]
            
            for i, format_strategy in enumerate(format_strategies):
                try:
                    ydl_opts = {
                        'format': format_strategy,
                        'outtmpl': str(self.output_dir / f'{safe_filename}.%(ext)s'),
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'verbose': False,
                        'no_warnings': False,
                    }
                    
                    print(f"🔄 Trying format strategy {i+1}: {format_strategy}")
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(youtube_url, download=True)
                        audio_file = ydl.prepare_filename(info)
                        audio_file = audio_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                        
                        # Verify the file was created
                        if os.path.exists(audio_file):
                            print(f"✅ Success with strategy {i+1}")
                            return {
                                'success': True,
                                'audio_path': audio_file,
                                'title': info.get('title', 'Unknown'),
                                'duration': info.get('duration', 0),
                                'uploader': info.get('uploader', 'Unknown'),
                                'thumbnail_url': info.get('thumbnail', ''),
                                'strategy_used': f"Strategy {i+1}: {format_strategy}"
                            }
                        else:
                            # Try alternative file extensions
                            for ext in ['.mp3', '.m4a', '.webm']:
                                alt_file = os.path.splitext(audio_file)[0] + ext
                                if os.path.exists(alt_file):
                                    print(f"✅ Found file with extension {ext}")
                                    return {
                                        'success': True,
                                        'audio_path': alt_file,
                                        'title': info.get('title', 'Unknown'),
                                        'duration': info.get('duration', 0),
                                        'uploader': info.get('uploader', 'Unknown'),
                                        'thumbnail_url': info.get('thumbnail', ''),
                                        'strategy_used': f"Strategy {i+1} with {ext}"
                                    }
                            
                            raise Exception("Downloaded file not found")
                
                except Exception as format_error:
                    print(f"❌ Strategy {i+1} failed: {format_error}")
                    if i == len(format_strategies) - 1:  # Last strategy
                        raise format_error
                    continue
            
            # If all strategies fail
            return {'success': False, 'error': 'All download strategies failed'}
            
        except Exception as e:
            error_msg = str(e)
            # Provide more user-friendly error messages
            if "Requested format is not available" in error_msg:
                error_msg = "The requested audio format is not available for this video. The video might be age-restricted, region-restricted, or live stream."
            elif "Private video" in error_msg:
                error_msg = "This video is private and cannot be downloaded."
            elif "This video is not available" in error_msg:
                error_msg = "This video is not available. It may have been removed or made private."
            
            return {'success': False, 'error': error_msg}
    
    def download_audio_manual_format(self, youtube_url, format_id):
        """Download audio with a specific format ID"""
        try:
            safe_filename = self.sanitize_filename("temp_audio")
            
            ydl_opts = {
                'format': format_id,
                'outtmpl': str(self.output_dir / f'{safe_filename}.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'verbose': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                audio_file = ydl.prepare_filename(info)
                audio_file = audio_file.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                return {
                    'success': True,
                    'audio_path': audio_file,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'thumbnail_url': info.get('thumbnail', '')
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}