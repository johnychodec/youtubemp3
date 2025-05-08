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
ALLOWED_USERS=user_id1,user_id2
```

Note: The bot uses password-based authentication for pCloud. Make sure to use a strong password and enable 2FA on your pCloud account for better security.

## Usage

1. Start the bot:
   ```