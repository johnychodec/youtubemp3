"""Main Telegram bot functionality."""
import os
import logging
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from pcloud import PyCloud
from .downloader import YouTubeDownloader
from .utils import (
    setup_temp_directory,
    cleanup_old_files,
    is_valid_youtube_url,
    get_safe_filename,
    format_file_size,
    get_video_id,
    get_file_size
)
import asyncio
import nest_asyncio
from queue import Queue
from threading import Event

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

class YouTubeBot:
    def __init__(self):
        # Validate required environment variables
        required_vars = ['TELEGRAM_BOT_TOKEN', 'PCLOUD_EMAIL', 'PCLOUD_PASSWORD', 'PCLOUD_BASE_FOLDER']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.pcloud_base_folder = os.getenv('PCLOUD_BASE_FOLDER')
        self.pcloud_link_expire_days = int(os.getenv('PCLOUD_LINK_EXPIRE_DAYS', '7'))
        self.allowed_users = [int(id) for id in os.getenv('ALLOWED_USER_IDS', '').split(',') if id]

        # Initialize pCloud with OAuth2
        try:
            self.pcloud = PyCloud(
                os.getenv('PCLOUD_EMAIL'),
                os.getenv('PCLOUD_PASSWORD')
            )
            self._ensure_pcloud_folder()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize pCloud: {e}")

        # Setup directories
        self.temp_dir = setup_temp_directory(os.getenv('TEMP_DIR', '/tmp/ytbtomp3'))
        
        # Initialize downloader
        self.downloader = YouTubeDownloader(self.temp_dir)

        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("cleanup", self.cleanup_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_youtube_url))

    def _ensure_pcloud_folder(self) -> None:
        """Ensure the base folder exists in pCloud."""
        try:
            # Create base folder if it doesn't exist
            folder_path = self.pcloud_base_folder.strip('/')
            current_path = ""
            
            for folder in folder_path.split('/'):
                if not folder:
                    continue
                if not current_path:
                    # Create first level folder
                    try:
                        self.pcloud.createfolder(name=folder)
                        current_path = folder
                    except Exception as e:
                        if "folder already exists" not in str(e).lower():
                            raise
                else:
                    # Create nested folder
                    try:
                        # First get the parent folder ID
                        parent_info = self.pcloud.listfolder(path=current_path)
                        if not parent_info or 'metadata' not in parent_info or 'folderid' not in parent_info['metadata']:
                            raise Exception(f"Could not find parent folder: {current_path}")
                        
                        parent_id = parent_info['metadata']['folderid']
                        self.pcloud.createfolder(name=folder, folderid=parent_id)
                        current_path = f"{current_path}/{folder}"
                    except Exception as e:
                        if "folder already exists" not in str(e).lower():
                            raise
            
            logger.info(f"Ensured pCloud folder exists: {self.pcloud_base_folder}")
        except Exception as e:
            raise RuntimeError(f"Failed to create pCloud folder structure: {e}")

    def _get_date_folder(self) -> str:
        """Get the current date folder path."""
        today = datetime.now().strftime('%Y-%m-%d')
        folder_path = f"{self.pcloud_base_folder.rstrip('/')}/{today}"
        try:
            # First get the parent folder ID
            parent_info = self.pcloud.listfolder(path=self.pcloud_base_folder)
            if not parent_info or 'metadata' not in parent_info or 'folderid' not in parent_info['metadata']:
                raise Exception(f"Could not find parent folder: {self.pcloud_base_folder}")
            
            parent_id = parent_info['metadata']['folderid']
            self.pcloud.createfolder(name=today, folderid=parent_id)
        except Exception as e:
            if "folder already exists" not in str(e).lower():
                raise
        return folder_path

    async def _upload_to_pcloud(self, file_path: str, title: str) -> str:
        """Upload file to pCloud and return confirmation message."""
        try:
            # Get target folder
            folder_path = self._get_date_folder()
            
            # Get folder ID
            folder_info = self.pcloud.listfolder(path=folder_path)
            if not folder_info or 'metadata' not in folder_info or 'folderid' not in folder_info['metadata']:
                raise Exception(f"Could not find folder: {folder_path}")
            
            folder_id = folder_info['metadata']['folderid']
            
            # Upload file
            with open(file_path, 'rb') as f:
                file_data = f.read()
                upload_result = self.pcloud.uploadfile(
                    folderid=folder_id,
                    filename=os.path.basename(file_path),
                    data=file_data
                )

            if not upload_result or 'fileids' not in upload_result:
                raise Exception("Upload failed: No file ID returned")

            file_id = upload_result['fileids'][0]
            logger.info(f"File uploaded successfully with ID: {file_id}")
            
            return f"✅ File uploaded successfully to pCloud. You can find it in your pCloud account."

        except Exception as e:
            logger.error(f"Error uploading to pCloud: {e}")
            raise

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        if not self.is_user_allowed(update.effective_user.id):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return

        await update.message.reply_text(
            "Welcome! Send me a YouTube link and I'll convert it to MP3.\n"
            "Large files will be shared via pCloud link."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        if not self.is_user_allowed(update.effective_user.id):
            return

        await update.message.reply_text(
            "Just send me a YouTube link and I'll convert it to MP3.\n"
            "Commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/cleanup - Clean up temporary files"
        )

    async def cleanup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clean up old temporary files."""
        if not self.is_user_allowed(update.effective_user.id):
            return

        cleanup_hours = int(os.getenv('CLEANUP_OLDER_THAN', '24'))
        cleanup_old_files(self.temp_dir, cleanup_hours)
        await update.message.reply_text("Cleanup completed!")

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        return len(self.allowed_users) == 0 or user_id in self.allowed_users

    async def handle_youtube_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle YouTube URLs."""
        if not self.is_user_allowed(update.effective_user.id):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return

        url = update.message.text
        if not is_valid_youtube_url(url):
            await update.message.reply_text("Please send a valid YouTube URL.")
            return

        # Send initial status message
        status_message = await update.message.reply_text("Processing your request...")

        try:
            # Get video info first
            video_info = self.downloader.extract_video_info(url)
            if not video_info:
                await status_message.edit_text("Could not get video information.")
                return

            # Estimate file size
            estimated_size = self.downloader.estimate_mp3_size(video_info)
            size_mb = estimated_size / (1024 * 1024)

            # Update status with video info
            await status_message.edit_text(
                f"Found: {video_info.title}\n"
                f"Duration: {video_info.duration} seconds\n"
                f"Estimated MP3 size: {size_mb:.1f}MB\n"
                "Starting download..."
            )

            # Create a queue for progress updates
            progress_queue = Queue()
            download_complete = Event()

            def progress_callback(progress: float, status: str):
                progress_queue.put((progress, status))

            # Start a background task to handle progress updates
            async def update_progress():
                while not download_complete.is_set():
                    try:
                        if not progress_queue.empty():
                            progress, status = progress_queue.get_nowait()
                            await status_message.edit_text(
                                f"Converting: {video_info.title}\n{status}\n"
                                f"Progress: {progress:.1f}%"
                            )
                    except Exception as e:
                        logger.error(f"Error updating progress: {e}")
                    await asyncio.sleep(0.5)

            # Start the progress update task
            progress_task = asyncio.create_task(update_progress())

            # Run the blocking operation in an executor
            output_path, error = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.downloader.download_audio(url, progress_callback)
            )

            # Signal completion and wait for progress task to finish
            download_complete.set()
            await progress_task

            if error:
                await status_message.edit_text(f"Error: {error}")
                return

            # Update status
            await status_message.edit_text(
                f"Download complete: {video_info.title}\n"
                "Uploading to pCloud..."
            )

            # Upload to pCloud
            try:
                upload_message = await self._upload_to_pcloud(output_path, video_info.title)
                
                # Send success message with link
                await status_message.edit_text(upload_message)
            except Exception as e:
                logger.error(f"Error uploading to pCloud: {e}")
                await status_message.edit_text(
                    "Error uploading the file to pCloud. Please try again later."
                )
            finally:
                # Clean up the temporary file
                try:
                    if output_path and os.path.exists(output_path):
                        os.remove(output_path)
                        logger.info(f"Cleaned up temporary file: {output_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {e}")

        except Exception as e:
            logger.error(f"Error processing YouTube URL: {e}")
            await status_message.edit_text(f"An error occurred: {str(e)}")

    def run(self):
        """Start the bot."""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Create and run the bot
    bot = YouTubeBot()
    bot.run()
