# YouTube to Telegram MP3 Converter

## Development Environment Setup


## Background and Motivation
The goal is to create a Telegram bot that:
1. Receives YouTube links in chat messages
2. Downloads the video and extracts the audio as MP3
3. Sends the MP3 file back to the same chat

This will be useful for personal use to easily convert YouTube videos to MP3 directly within Telegram.

## Tech Stack
1. Runtime: Python 3.x
2. Core Dependencies:
   - python-telegram-bot: Telegram bot integration
   - python-dotenv: Environment variable management
   - yt-dlp: YouTube video downloading
   - ffmpeg-python: Audio conversion wrapper
   - pcloud: pCloud API integration for file storage
   - requests: For HTTP operations
3. System Dependencies:
   - yt-dlp: YouTube video downloading
   - ffmpeg: Audio conversion

## Key Challenges and Analysis
1. YouTube video downloading and audio extraction
   - Using yt-dlp for reliable YouTube video downloading
   - Must ensure proper audio extraction without quality loss
   - Need to handle temporary file storage
   - Storage management:
     - Implement cleanup of temporary files after processing:
       * Clean up downloaded video files immediately after MP3 extraction
       * Clean up MP3 files after successful upload to Telegram
       * Implement cleanup on process termination (signal handlers)
       * Add periodic cleanup of orphaned files (files older than X hours)
       * Use dedicated temp directory with proper permissions
     - Monitor disk space usage
     - Set maximum file size limits for downloads
     - Implement storage quota per user if needed
   - File size management for Telegram limits:
     * Check estimated file size before download (using yt-dlp info)
     * Implement audio compression strategies:
       - Reduce bitrate (e.g., 192kbps or 128kbps)
       - Use more efficient audio codec if needed
       - Split large files into parts (e.g., 45MB chunks)
     * Notify user when original audio quality needs to be reduced
     * Provide alternative delivery method for files > 50MB (e.g., direct download link)

2. Telegram bot implementation
   - Need to set up a Telegram bot
   - Handle message events and URL detection
   - Manage file uploads to Telegram
   - Handle file size limits (Telegram has a 50MB limit for bots)
   - Show progress updates in chat
   - No need to open inbound ports as bot uses polling mechanism
   - Ensure stable outbound internet connection for bot operation
   - Polling considerations:
     - Default polling interval is 1 request every 1-2 seconds
     - Telegram allows up to 30 messages per second
     - Use python-telegram-bot's built-in rate limiting
     - Implement exponential backoff for error handling
     - Long polling timeout should be 30-50 seconds for efficiency

3. Error handling
   - Handle invalid YouTube URLs
   - Handle network issues
   - Handle file conversion errors
   - Handle Telegram API errors
   - Provide clear error messages in chat

4. Network Considerations
   - Bot uses outbound HTTPS connections to Telegram servers
   - No port forwarding or inbound ports needed
   - Ensure outbound HTTPS (port 443) is not blocked
   - Consider implementing connection retry logic for network interruptions
   - Monitor network usage for large file transfers

5. Security and Rate Limiting
   - Implement user access control (whitelist specific users/chats)
   - Rate limit requests per user to prevent abuse
   - Validate YouTube URLs before processing
   - Sanitize file names and paths
   - Secure storage of bot token and sensitive data
   - Monitor for suspicious usage patterns

6. Process Management and Reliability
   - Implement graceful shutdown handling
   - Add logging for debugging and monitoring
   - Consider using systemd service for auto-restart
   - Handle concurrent requests properly
   - Implement request queuing if needed
   - Add periodic health checks
   - Monitor memory usage during conversions

7. Cloud Storage Integration (pCloud)
   - Authentication:
     * Use password-based authentication (simpler for personal use)
     * Initial login requires 2FA code via email
     * Store credentials securely in .env file:
       - PCLOUD_EMAIL=your-email@example.com
       - PCLOUD_PASSWORD=your-password
     * One-time authentication setup:
       1. First run will request 2FA code
       2. After successful 2FA, the connection remains active
       3. No need to re-authenticate unless session expires
   - File management:
     * Create dedicated folder for bot uploads (e.g., "youtube_mp3_bot")
     * Organize files by date (YYYY-MM-DD folders)
     * Generate shareable links with configurable expiration
     * Implement automatic cleanup based on age or storage quota
     * Track upload progress
   - Link sharing:
     * Generate short-lived download links (configurable expiration)
     * Include file metadata in messages:
       - Title
       - Duration
       - File size
       - Audio quality
       - Link expiration time
     * Option to regenerate expired links
     * Include direct pCloud link and web player link when available

## High-level Task Breakdown

### Phase 1: Setup and Basic Structure
- [ ] Initialize Python project with requirements.txt
  - Success criteria:
    - requirements.txt contains all necessary dependencies with versions
    - All dependencies can be installed
- [ ] Install required Python dependencies
- [ ] Create basic project structure:
  - src/
    - bot.py (main bot logic)
    - downloader.py (yt-dlp wrapper)
    - utils.py (helper functions)
  - .env (for Telegram bot token)
  - .gitignore
- [ ] Set up environment variables for Telegram bot token
- [ ] Add logging configuration
  - Success criteria:
    - Logs include timestamp, severity level, and context
    - Logs are written to both console and file
    - Log rotation is configured
- [ ] Set up systemd service
  - Success criteria:
    - Service auto-starts on boot
    - Service auto-restarts on failure
    - Proper logging to system journal

### Phase 2: Telegram Bot Setup
- [ ] Create Telegram bot using BotFather
- [ ] Implement basic bot message handling
- [ ] Add YouTube URL detection and validation
- [ ] Add progress message updates in chat
- [ ] Implement user access control
- [ ] Add rate limiting per user
- [ ] Add request queuing system

### Phase 3: YouTube Download and Conversion
- [ ] Implement YouTube video download using yt-dlp
  - Success criteria:
    * File size is estimated before download
    * Downloads are rejected if estimated size is too large
    * User is notified of size issues before processing
- [ ] Implement audio extraction to MP3
  - Success criteria:
    * Audio quality settings are configurable
    * Automatic bitrate adjustment for large files
    * Files are split if they exceed size limit
    * Original quality is preserved when possible
- [ ] Add file size management
  - Success criteria:
    * Files over 50MB are detected before upload
    * Automatic compression is applied when needed
    * User is notified of quality adjustments
    * Split files are properly labeled (Part 1, Part 2, etc.)
    * Alternative delivery option for large files works
- [ ] Add temporary file management
  - Success criteria:
    * Dedicated temp directory is created with proper permissions
    * Video files are deleted immediately after MP3 extraction
    * MP3 files are deleted after successful Telegram upload
    * Signal handlers clean up files on process termination
    * Periodic cleanup job removes old files (configurable time threshold)
    * No temporary files remain after process crashes
    * Disk space is monitored before and after operations
- [ ] Add error handling for download/conversion process
- [ ] Implement storage management
  - Success criteria:
    - Temporary files are cleaned up after processing
    - Disk space is monitored
    - Downloads are limited by file size
- [ ] Add health monitoring
  - Success criteria:
    - Memory usage is monitored
    - Disk space is checked before downloads
    - Long-running processes are detected

### Phase 4: File Storage and Delivery
- [ ] Set up pCloud integration
  - Success criteria:
    * Password authentication works
    * 2FA setup process is documented
    * Bot can create and manage folders
    * Files can be uploaded successfully
    * Shareable links can be generated
- [ ] Implement file management
  - Success criteria:
    * Dedicated bot folder is created
    * Files are organized in date-based folders
    * Upload progress is tracked and reported
    * Storage usage is monitored
- [ ] Implement link sharing
  - Success criteria:
    * Links are generated with proper expiration
    * File metadata is included in messages
    * Links work reliably
    * Users can request new links for existing files

### Phase 5: Integration and Testing
- [ ] Combine all components
  - Success criteria:
    * Full workflow works: YouTube → MP3 → pCloud → Link shared in Telegram
    * Progress updates are shown throughout the process
    * Error handling works properly
    * File cleanup works as expected
- [ ] Add monitoring
  - Success criteria:
    * Storage usage is tracked
    * Error rates are monitored
    * Link usage is tracked
    * System performance is monitored
- [ ] Documentation
  - Success criteria:
    * Setup process is documented
    * Usage instructions are clear
    * Error messages are helpful
    * Maintenance procedures are documented

# Project Status Board

## Completed Tasks
- [x] Install Python 3.11
- [x] Install pip
- [x] Install required Python packages
- [x] Install ffmpeg
- [x] Set up project directory structure
- [x] Set up Telegram bot token
- [x] Implement basic Telegram bot setup
- [x] Implement message handling
- [x] Implement YouTube URL detection and validation
- [x] Set up yt-dlp integration for video downloading
- [x] Implement audio extraction to MP3
- [x] Implement file size estimation and management
- [x] Implement progress updates in chat
- [x] Set up pCloud integration for large files
- [x] Implement temporary file management
- [x] Implement file cleanup after processing
- [x] Implement basic error handling
- [x] Set up logging configuration

## Next Steps
- [ ] Add comprehensive error handling for edge cases
- [ ] Add health monitoring
- [ ] Add documentation
- [ ] Add user feedback and statistics
- [ ] Add rate limiting
- [ ] Add support for playlists
- [ ] Add support for video quality selection
- [ ] Add support for custom output formats

# Current Status / Progress Tracking
The bot is now running successfully with the following features working:
1. Telegram bot integration
2. YouTube URL validation
3. Video downloading and MP3 conversion
4. pCloud integration for large files
5. Progress updates in chat
6. Temporary file management
7. Basic error handling
8. Logging

The bot is ready for testing with actual YouTube URLs. Users can send YouTube links to the bot, and it will:
1. Validate the URL
2. Download the video
3. Convert it to MP3
4. Upload to pCloud if the file is large
5. Send the file or pCloud link back to the user
6. Clean up temporary files

# Executor's Feedback or Assistance Requests
The bot is running successfully. No immediate assistance is needed. Ready to proceed with implementing additional features or improvements.

# Lessons
1. Always check for required environment variables before running the bot
2. Use proper error handling for external service integrations (Telegram, pCloud)
3. Implement proper logging for debugging and monitoring
4. Clean up temporary files to prevent disk space issues
5. Use relative imports for better code organization
6. Include info useful for debugging in the program output
7. Read the file before you try to edit it
8. If there are vulnerabilities that appear in the terminal, run npm audit before proceeding
9. Always ask before using the -force git command

# Deployment Instructions for Raspberry Pi

## Prerequisites
1. Raspberry Pi running Raspberry Pi OS (preferably latest version)
2. SSH access to your Raspberry Pi
3. Python 3.11 or later installed
4. ffmpeg installed
5. rsync installed on both local machine and Raspberry Pi

## Setup Steps

### 1. Install rsync (if not already installed)
```bash
# On your local machine (if using macOS)
brew install rsync

# On Raspberry Pi
sudo apt-get update
sudo apt-get install rsync
```

### 2. Create Project Directory on Raspberry Pi
```bash
ssh pi@your_raspberry_pi_ip
mkdir -p ~/projects/YtbToTelegram
```

### 3. Copy Files to Raspberry Pi
```bash
# From your local machine, in the project directory
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.env' ./ dietpi@100.82.186.73:~/ytbtomp3
```

### 4. Create and Activate Virtual Environment
```bash
# SSH into Raspberry Pi
ssh pi@your_raspberry_pi_ip
cd ~/projects/YtbToTelegram

# Install virtualenv if not already installed
sudo apt-get update
sudo apt-get install python3-venv

# Create virtual environment
python3 -m venv ytbtomp3

# Activate virtual environment
source ytbtomp3/ytbtomp3/bin/activate
```

### 5. Install System Dependencies
```bash
# Install ffmpeg
sudo apt-get install ffmpeg
```

### 6. Install Python Dependencies
```bash
# Make sure you're in the virtual environment
source ytbtomp3/ytbtomp3/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 7. Set Up Environment Variables
```bash
# Create .env file
nano .env

# Add the following content (replace with your actual values):
TELEGRAM_BOT_TOKEN=your_bot_token_here
PCLOUD_EMAIL=your_pcloud_email_here
PCLOUD_PASSWORD=your_pcloud_password_here
PCLOUD_BASE_FOLDER=/YouTubeToMP3
PCLOUD_LINK_EXPIRE_DAYS=7
TEMP_DIR=/tmp/ytbtomp3
CLEANUP_OLDER_THAN=24
LOG_LEVEL=INFO
ALLOWED_USER_IDS=your_telegram_user_id_here
```

### 8. Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/ytb-to-telegram.service

# Add the following content:
[Unit]
Description=YouTube to Telegram MP3 Converter Bot
After=network.target

[Service]
Type=simple
User=dietpi
WorkingDirectory=/home/jnhr/pythonprojects/youtubemp3
Environment=PATH=/home/jnhr/pythonprojects/ytbtomp3/ytbtomp3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/home/dietpi/ytbtomp3
ExecStart=/home/dietpi/ytbtomp3/ytbtomp3/bin/python -m src.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# After creating the file, reload systemd
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable ytb-to-telegram

# Start the service
sudo systemctl start ytb-to-telegram

# Check status
sudo systemctl status ytb-to-telegram
```