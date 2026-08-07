# Discord DM utility bot

This project is a small [nextcord](https://nextcord.readthedocs.io/) bot for
moderation and support workflows. It provides `/dm` and `<prefix>dm` commands.
Each command sends **one** direct message, requires the caller to have the
Manage Messages permission, rate-limits each caller, and disables mentions in
the delivered message.

## Setup on Railway

1. Create a bot application in the
   [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable the **Message Content Intent** and **Server Members Intent** on the
   bot's **Privileged Gateway Intents** page.
3. Add the bot to your server with the `bot` and `applications.commands` scopes.
   The bot needs permission to view the server and send messages.
4. In Railway, add `TOKEN` as a service variable. Never commit a Discord token
   to `.env` or source control.
5. Enable Discord Developer Mode, right-click your own account, choose **Copy
   User ID**, and add that number as the Railway `OWNER_ID` variable. Only that
   account can use `/dm` in a direct message with the bot.
6. `PREFIX` defaults to `!`. `GUILD_ID` is retained for existing deployments,
   but `/dm` is global so it can work in DMs; a new global command can take up
   to an hour to appear.
7. Set the Railway start command to `python bot.py` if Railway does not detect
   the included `Procfile` automatically.

This is a long-running worker and does not expose an HTTP port. Railway may
show no web URL for the service; a healthy deployment is indicated by the
startup log showing that the bot logged in successfully.

The included `runtime.txt` pins Railway to Python 3.12.11. This is required
because Python 3.13 removed the standard-library `audioop` module that
Nextcord still imports at startup.

The requirements also pin `setuptools` below version 81 because Nextcord 2.x
uses `pkg_resources`, which newer setuptools releases removed.

## Local setup

```bash
cp .env.example .env
python -m pip install -r requirements.txt
python bot.py
```

## Commands

- `/dm message:Hello times:1 username:@user`
- `!dm @user content` (or the prefix you configured)

The `times` option is required for compatibility with the requested command
shape but only accepts `1`; bulk or repeated DM sending is intentionally not
supported.

With `OWNER_ID` configured, the owner can run `/dm` directly in a DM with the
bot. The bot sends the message to the selected username and sends the owner an
identical copy. Discord does not support a bot creating one shared private DM
between two other users, and this bot cannot log in as or impersonate a
personal account.

The recipient must allow direct messages from the bot. Discord may still
reject delivery when the recipient has DMs disabled, blocked the bot, or the
bot cannot resolve the user.