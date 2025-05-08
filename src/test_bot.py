"""Test suite for the Telegram bot and downloader integration."""
import os
import logging
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, filters
from .bot import YouTubeBot
from .downloader import YouTubeDownloader
from .utils import VideoInfo

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Test data
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
TEST_VIDEO_INFO = VideoInfo(
    id="dQw4w9WgXcQ",
    title="Rick Astley - Never Gonna Give You Up",
    duration=212,  # 3:32
    filesize_approx=3_145_728,  # ~3MB
    is_age_restricted=False,
    formats=[],
    thumbnail="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    description="Test description",
    uploader="Test uploader"
)

@pytest.fixture
def mock_env():
    """Set up test environment variables."""
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
    os.environ['PCLOUD_EMAIL'] = 'test@example.com'
    os.environ['PCLOUD_PASSWORD'] = 'test_password'
    os.environ['PCLOUD_BASE_FOLDER'] = '/test_folder'
    os.environ['ALLOWED_USER_IDS'] = '123456,789012'
    yield
    # Clean up
    for key in ['TELEGRAM_BOT_TOKEN', 'PCLOUD_EMAIL', 'PCLOUD_PASSWORD', 'PCLOUD_BASE_FOLDER', 'ALLOWED_USER_IDS']:
        os.environ.pop(key, None)

@pytest.fixture
def mock_update():
    """Create a mock Telegram update."""
    update = MagicMock(spec=Update)
    message = MagicMock(spec=Message)
    user = MagicMock(spec=User)
    chat = MagicMock(spec=Chat)
    
    user.id = 123456  # Allowed user ID
    chat.id = 123456
    message.from_user = user
    message.chat = chat
    message.text = TEST_VIDEO_URL
    update.message = message
    update.effective_user = user
    
    # Mock the reply_text method
    message.reply_text = AsyncMock()
    # Mock edit_text for status updates
    message.reply_text.return_value.edit_text = AsyncMock()
    
    return update

@pytest.fixture
def mock_context():
    """Create a mock context."""
    return MagicMock(spec=ContextTypes.DEFAULT_TYPE)

@pytest_asyncio.fixture
async def bot(mock_env):
    """Create a YouTubeBot instance with mocked dependencies."""
    with patch('pcloud.PyCloud') as mock_pcloud:
        # Mock pCloud methods
        mock_pcloud.return_value.createfolderifnotexists = MagicMock()
        mock_pcloud.return_value.uploadfile = MagicMock(return_value={'fileids': [12345]})
        mock_pcloud.return_value.getfilepublink = MagicMock(return_value={'link': 'https://test.link'})
        
        bot_instance = YouTubeBot()
        return bot_instance

@pytest.mark.asyncio
async def test_handle_youtube_url_success(bot, mock_update, mock_context):
    """Test successful YouTube URL handling."""
    # Mock downloader methods
    bot.downloader.extract_video_info = MagicMock(return_value=TEST_VIDEO_INFO)
    bot.downloader.estimate_mp3_size = MagicMock(return_value=3_145_728)  # ~3MB
    bot.downloader.download_audio = MagicMock(return_value=('/tmp/test.mp3', None))
    
    # Test URL handling
    await bot.handle_youtube_url(mock_update, mock_context)
    
    # Verify video info was extracted
    bot.downloader.extract_video_info.assert_called_once_with(TEST_VIDEO_URL)
    
    # Verify size estimation was performed
    bot.downloader.estimate_mp3_size.assert_called_once_with(TEST_VIDEO_INFO)
    
    # Verify download was initiated
    bot.downloader.download_audio.assert_called_once()
    
    # Verify status messages were sent
    status_message = mock_update.message.reply_text.return_value
    status_message.edit_text.assert_called()
    
    # Verify final message contains success indicators
    final_call_args = status_message.edit_text.call_args_list[-1].args[0]
    assert "✅ File uploaded successfully to pCloud" in final_call_args
    assert "You can find it in your pCloud account" in final_call_args

@pytest.mark.asyncio
async def test_handle_youtube_url_unauthorized(bot, mock_update, mock_context):
    """Test unauthorized user handling."""
    # Set user ID to unauthorized
    mock_update.effective_user.id = 999999
    
    await bot.handle_youtube_url(mock_update, mock_context)
    
    # Verify unauthorized message was sent
    mock_update.message.reply_text.assert_called_once_with(
        "Sorry, you are not authorized to use this bot."
    )

@pytest.mark.asyncio
async def test_handle_youtube_url_invalid_url(bot, mock_update, mock_context):
    """Test invalid URL handling."""
    mock_update.message.text = "https://not-youtube.com/watch?v=123"
    
    await bot.handle_youtube_url(mock_update, mock_context)
    
    # Verify invalid URL message was sent
    mock_update.message.reply_text.assert_called_once_with(
        "Please send a valid YouTube URL."
    )

@pytest.mark.asyncio
async def test_handle_youtube_url_download_error(bot, mock_update, mock_context):
    """Test download error handling."""
    # Mock downloader to simulate error
    bot.downloader.extract_video_info = MagicMock(return_value=TEST_VIDEO_INFO)
    bot.downloader.estimate_mp3_size = MagicMock(return_value=3_145_728)
    bot.downloader.download_audio = MagicMock(return_value=(None, "Download failed"))
    
    await bot.handle_youtube_url(mock_update, mock_context)
    
    # Verify error message was sent
    status_message = mock_update.message.reply_text.return_value
    status_message.edit_text.assert_called_with("Error: Download failed")

@pytest.mark.asyncio
async def test_handle_youtube_url_upload_error(bot, mock_update, mock_context):
    """Test pCloud upload error handling."""
    # Mock successful download but failed upload
    bot.downloader.extract_video_info = MagicMock(return_value=TEST_VIDEO_INFO)
    bot.downloader.estimate_mp3_size = MagicMock(return_value=3_145_728)
    bot.downloader.download_audio = MagicMock(return_value=('/tmp/test.mp3', None))
    
    # Mock pCloud upload to fail
    bot._upload_to_pcloud = AsyncMock(side_effect=Exception("Upload failed"))
    
    await bot.handle_youtube_url(mock_update, mock_context)
    
    # Verify error message was sent
    status_message = mock_update.message.reply_text.return_value
    status_message.edit_text.assert_called_with(
        "Error uploading the file to pCloud. Please try again later."
    )

async def test_bot():
    """Test the YouTube bot functionality."""
    try:
        # Initialize bot
        bot = YouTubeBot()
        
        # Test /start command
        print("Testing /start command...")
        await bot.start(Update(update_id=1), ContextTypes.DEFAULT_TYPE)
        
        # Test /help command
        print("\nTesting /help command...")
        await bot.help_command(Update(update_id=1), ContextTypes.DEFAULT_TYPE)
        
        # Test message handling
        print("\nTesting message handling...")
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        await bot.handle_message(Update(update_id=1, message=Message(text=test_url)), ContextTypes.DEFAULT_TYPE)
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test_bot: {str(e)}")
        raise

if __name__ == '__main__':
    asyncio.run(test_bot()) 