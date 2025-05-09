"""
YouTube video downloader and audio converter.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable
from dataclasses import dataclass
import yt_dlp
from dotenv import load_dotenv
import ffmpeg
from .utils import get_safe_filename, format_file_size

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Audio configuration
DEFAULT_BITRATE = 128  # Always use 128kbps for consistent quality and file size

@dataclass
class VideoInfo:
    """Data class to store video metadata."""
    id: str
    title: str
    duration: int  # in seconds
    filesize_approx: int  # in bytes
    is_age_restricted: bool
    formats: list
    thumbnail: str
    description: str
    uploader: str

class DownloadError(Exception):
    """Custom exception for download-related errors."""
    pass

class YouTubeDownloader:
    """Handles YouTube video downloads and audio extraction."""

    def __init__(self, temp_dir: str = 'temp'):
        """
        Initialize the downloader with configuration.
        
        Args:
            temp_dir: Directory for temporary files. Defaults to env TEMP_DIR or '/tmp/ytbtomp3'
        """
        load_dotenv()  # Load environment variables
        
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'outtmpl': str(Path(self.temp_dir) / '%(id)s.%(ext)s'),
        }
        
        logger.info(f"Initialized YouTubeDownloader with temp_dir: {self.temp_dir}")

    def _ensure_temp_dir(self) -> None:
        """Create temporary directory if it doesn't exist."""
        try:
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.debug(f"Ensured temp directory exists: {self.temp_dir}")
        except OSError as e:
            logger.error(f"Failed to create temp directory: {e}")
            raise DownloadError(f"Could not create temp directory: {e}")

    def extract_video_info(self, url: str) -> VideoInfo:
        """
        Extract metadata from a YouTube video URL.
        
        Args:
            url: YouTube video URL
            
        Returns:
            VideoInfo object containing video metadata
            
        Raises:
            DownloadError: If video info extraction fails
        """
        logger.info(f"Extracting video info for URL: {url}")
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_info = VideoInfo(
                    id=info['id'],
                    title=info['title'],
                    duration=info['duration'],
                    filesize_approx=info.get('filesize_approx', 0),
                    is_age_restricted=info.get('age_limit', 0) > 0,
                    formats=info['formats'],
                    thumbnail=info.get('thumbnail', ''),
                    description=info.get('description', ''),
                    uploader=info.get('uploader', 'Unknown')
                )
                
                logger.info(f"Successfully extracted info for video: {video_info.title}")
                logger.debug(f"Video details: duration={video_info.duration}s, "
                           f"size={video_info.filesize_approx/1024/1024:.2f}MB")
                
                return video_info
                
        except Exception as e:
            error_msg = f"Failed to extract video info: {str(e)}"
            logger.error(error_msg)
            raise DownloadError(error_msg)

    def estimate_mp3_size(self, video_info: VideoInfo, bitrate: int = DEFAULT_BITRATE) -> int:
        """
        Estimate the final MP3 file size based on video duration and target bitrate.
        
        Args:
            video_info: VideoInfo object containing video metadata
            bitrate: Target MP3 bitrate in kbps (default: 128)
            
        Returns:
            Estimated file size in bytes
        """
        # Estimate MP3 size: (bitrate * 1000 / 8) * duration
        # Add 1% overhead for MP3 headers and metadata
        estimated_size = int((bitrate * 1000 / 8) * video_info.duration * 1.01)
        
        logger.info(f"Estimated MP3 size for {video_info.title}: "
                   f"{estimated_size/1024/1024:.2f}MB at {bitrate}kbps")
        
        return estimated_size

    def get_video_info(self, url: str) -> Optional[dict]:
        """Get video information without downloading."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'filesize_approx': info.get('filesize_approx'),
                    'thumbnail': info.get('thumbnail')
                }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None

    def download_audio(
        self,
        url: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Download and convert video to MP3.
        
        Args:
            url: YouTube video URL
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (output_path, error_message). If successful, error_message is None.
            If failed, output_path is None and error_message contains the error.
        """
        logger.info(f"Starting download for URL: {url}")
        
        try:
            # Get video info first
            info = self.extract_video_info(url)
            safe_title = get_safe_filename(info.title)
            output_template = os.path.join(self.temp_dir, safe_title)
            output_path = f"{output_template}.mp3"

            def progress_hook(d):
                if d['status'] == 'downloading' and progress_callback:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        progress = (downloaded / total) * 100
                        progress_callback(progress, f"Downloading: {format_file_size(downloaded)} / {format_file_size(total)}")
                elif d['status'] == 'finished' and progress_callback:
                    progress_callback(100, "Download complete, converting to MP3...")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(DEFAULT_BITRATE),
                }],
                'outtmpl': output_template,  # yt-dlp will append the extension
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'ffmpeg_location': os.getenv('FFMPEG_PATH', '/usr/bin/ffmpeg')  # Use environment variable with fallback
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Downloading and converting video: {info.title}")
                ydl.download([url])
                
                # Wait a moment for file operations to complete
                import time
                time.sleep(1)
                
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logger.info(f"Successfully created MP3: {output_path} ({format_file_size(file_size)})")
                    return output_path, None
                else:
                    # Check if the file exists with any extension
                    possible_files = [f for f in os.listdir(self.temp_dir) if f.startswith(safe_title)]
                    if possible_files:
                        error_msg = f"Found unexpected files: {', '.join(possible_files)}"
                    else:
                        error_msg = "MP3 file was not created"
                    logger.error(error_msg)
                    return None, error_msg

        except Exception as e:
            error_msg = f"Error downloading/converting video: {str(e)}"
            logger.error(error_msg)
            return None, error_msg

    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a file from the temporary directory.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")
            return False

    def get_audio_duration(self, file_path: str) -> Optional[float]:
        """Get duration of audio file in seconds."""
        try:
            probe = ffmpeg.probe(file_path)
            return float(probe['streams'][0]['duration'])
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None

    def get_audio_bitrate(self, file_path: str) -> Optional[int]:
        """Get audio bitrate in kbps."""
        try:
            probe = ffmpeg.probe(file_path)
            return int(probe['streams'][0]['bit_rate']) // 1000
        except Exception as e:
            logger.error(f"Error getting audio bitrate: {e}")
            return None

if __name__ == '__main__':
    # Test the implementation with the test URL from environment
    test_url = os.getenv('YOUTUBE_TEST_URL')
    if test_url:
        try:
            downloader = YouTubeDownloader()
            
            # First get video info
            info = downloader.extract_video_info(test_url)
            print(f"\nVideo Information:")
            print(f"Title: {info.title}")
            print(f"Duration: {info.duration} seconds")
            print(f"Uploader: {info.uploader}")
            
            # Estimate size
            size_mb = downloader.estimate_mp3_size(info) / 1024 / 1024
            print(f"\nEstimated MP3 size: {size_mb:.2f}MB")
            
            # Define progress callback
            def show_progress(progress: float, status: str):
                print(f"\rProgress: {progress:.1f}% - {status}", end='', flush=True)
            
            # Download and convert
            print("\nDownloading and converting to MP3...")
            output_path, error = downloader.download_audio(test_url, show_progress)
            
            if error:
                print(f"\nError: {error}")
            else:
                # Get actual file info
                file_size = os.path.getsize(output_path)
                print(f"\n\nSuccess! Created MP3: {os.path.basename(output_path)}")
                print(f"File size: {format_file_size(file_size)}")
                
                # Clean up
                if input("\nClean up the MP3 file? (y/n): ").lower() == 'y':
                    if downloader.cleanup_file(output_path):
                        print("File cleaned up successfully")
                    else:
                        print("Failed to clean up file")
                
        except DownloadError as e:
            print(f"Error: {e}")
    else:
        print("No test URL found in environment variables")
