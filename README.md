# YouTube to MP3 Converter Bot

A Telegram bot that converts YouTube videos to MP3 files and uploads them to your pCloud.

## Features

- Convert YouTube videos to MP3
- Progress updates during conversion
- Automatic cleanup of temporary files

## Requirements

- Ffmpeg
- Python 3.11+
- pCloud account
- A Telegram Bot Token

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` and fill in your credentials:   

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

Note: The bot uses password-based authentication for pCloud. I didn't try that with other means.

### Access Control
- If `ALLOWED_USER_IDS` is not set or empty, the bot will be accessible to all users
- To restrict access, set `ALLOWED_USER_IDS` to a comma-separated list of Telegram user IDs
- You can get your Telegram user ID by sending a message to @userinfobot


### Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/ytb-to-telegram.service

# Add the following content - EXAMPLE:
[Unit]
Description=YouTube to Telegram MP3 Converter Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/fullpath/pythonprojects/youtubemp3
Environment=PATH=/fullpath/pythonprojects/ytbtomp3/ytbtomp3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=/fullpath/ytbtomp3
ExecStart=/fullpath/ytbtomp3/ytbtomp3/bin/python -m src.bot
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