"""Utility functions for the YouTube to MP3 converter."""
import os
import re
import logging
from typing import Optional, Union, List
from datetime import datetime, timedelta
import math
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

@dataclass
class VideoInfo:
    """Information about a YouTube video."""
    id: str
    title: str
    duration: int
    filesize_approx: int
    is_age_restricted: bool
    formats: List[dict]
    thumbnail: str
    description: str
    uploader: str

def setup_temp_directory(temp_dir: str = "./tmp") -> str:
    """Create temporary directory if it doesn't exist."""
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def cleanup_old_files(temp_dir: str, hours: int = 24) -> None:
    """Remove files older than specified hours from temp directory."""
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath):
                if datetime.fromtimestamp(os.path.getmtime(filepath)) < cutoff:
                    os.remove(filepath)
                    logger.info(f"Removed old file: {filepath}")
    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")

def is_valid_youtube_url(url: str) -> bool:
    """Check if the URL is a valid YouTube URL."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(re.match(youtube_regex, url))

def get_safe_filename(filename: str) -> str:
    """
    Convert a string into a safe filename by removing or replacing invalid characters.
    
    Args:
        filename: The original filename
        
    Returns:
        A sanitized filename safe for all operating systems
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces and dots with underscores, except the last dot
    parts = filename.rsplit('.', 1)
    parts[0] = re.sub(r'[\s.]+', '_', parts[0])
    # Join back with the extension if it existed
    return '.'.join(parts) if len(parts) > 1 else parts[0]

def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.23 MB")
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ("B", "KB", "MB", "GB", "TB")
    magnitude = int(math.floor(math.log(size_bytes, 1024)))
    val = size_bytes / math.pow(1024, magnitude)
    
    return f"{val:.2f} {size_names[magnitude]}"

def get_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:be\/)([0-9A-Za-z_-]{11}).*'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_file_size(file_path: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)
