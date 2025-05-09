# YouTube to Telegram MP3 Converter Bot

A Telegram bot that converts YouTube videos to MP3 files and sends them back to you.

## Features

- Convert YouTube videos to MP3
- Handle videos larger than Telegram's 50MB limit via pCloud links
- Progress updates during conversion
- Automatic cleanup of temporary files

## Requirements

- Python 3.11+
- ffmpeg
- A Telegram Bot Token
- pCloud account

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

## Configuration

Create a `.env` file with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
PCLOUD_EMAIL=your_pcloud_email
PCLOUD_PASSWORD=your_pcloud_password
PCLOUD_BASE_FOLDER=your_pcloud_folder
PCLOUD_LINK_EXPIRE_DAYS=7
TEMP_DIR=/tmp/ytbtomp3
CLEANUP_OLDER_THAN=24
LOG_LEVEL=INFO
ALLOWED_USER_IDS=user_id1,user_id2  # Optional: Comma-separated list of allowed user IDs. If not set, all users are allowed.
FFMPEG_PATH=/usr/bin/ffmpeg
DEFAULT_AUDIO_BITRATE=128
POLLING_INTERVAL=1.0
```

Note: The bot uses password-based authentication for pCloud. Make sure to use a strong password and enable 2FA on your pCloud account for better security.

### Access Control
- If `ALLOWED_USER_IDS` is not set or empty, the bot will be accessible to all users
- To restrict access, set `ALLOWED_USER_IDS` to a comma-separated list of Telegram user IDs
- You can get your Telegram user ID by sending a message to @userinfobot

## Usage

1. Start the bot:
   ```