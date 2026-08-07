# Discord DM utility bot

This project is a small [nextcord](https://nextcord.readthedocs.io/) bot for
moderation and support workflows. It provides `/dm` and `<prefix>dm` commands.
Each command sends **one** direct message, requires the caller to have the
Manage Messages permission, rate-limits each caller, and disables mentions in
the delivered message.

## Setup on Replit

1. Create a bot application in the
   [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable the **Message Content Intent** and **Server Members Intent** on the
   bot's **Privileged Gateway Intents** page.
3. Add the bot to your server with the `bot` and `applications.commands` scopes.
   The bot needs permission to view the server and send messages.
4. Add `TOKEN` as a Replit Secret. Never commit a Discord token to `.env` or
   source control.
5. Add `GUILD_ID` as an environment variable for the server where you are
   testing. This makes `/dm` appear quickly. `PREFIX` defaults to `!`.

## Local setup

```bash
cp .env.example .env
python -m pip install -r requirements.txt
python bot.py
```

## Commands

- `/dm user content`
- `!dm @user content` (or the prefix you configured)

The recipient must allow direct messages from the bot. Discord may still
reject delivery when the recipient has DMs disabled, blocked the bot, or the
bot cannot resolve the user.