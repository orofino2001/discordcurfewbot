🌙 Discord Bedtime Bot
Kicks users from voice channels at their bedtime

📜 Legal
Privacy Policy
Last Updated: 28/08/25
This bot:

Stores only necessary data (user IDs, timezones, and bedtimes) in memory.

Does not log or store voice channel activity, messages, or other sensitive data.

Data is deleted when the bot restarts (unless a database is implemented  later).

For transparency:

Users can view their stored data via !mybedtime.

Users can delete data via !disable or by kicking the bot from the server.

Terms of Service
By using this bot, users agree:

The bot may disconnect them from voice channels at their set bedtime.

Misuse (e.g., spam) may result in blacklisting.

The bot has no affiliation with Discord Inc.

🛠️ Setup
Clone this repo

Install dependencies:

bash
pip install -r requirements.txt
Configure:

For Replit: Use 🔒 Secrets (DISCORD_TOKEN = your bot token).

Local use: Create .env:

ini
DISCORD_TOKEN=your_bot_token_here
🔐 Security Reminder
Never commit/share your .env file or token.

Regenerate your token immediately if exposed.

