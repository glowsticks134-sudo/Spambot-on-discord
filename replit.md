# Project overview

This is a Python `nextcord` Discord bot. The supported commands are `/dm` and
`<prefix>dm`; each sends one non-pinging direct message to a selected user.
Commands are restricted to members with the Manage Messages permission and
include a per-user cooldown.

## Running on Replit

The project uses Python 3.12 and the dependencies in `requirements.txt`.
Create a console workflow with:

```text
python bot.py
```

Required configuration:

- `TOKEN`: Discord bot token, stored as a Replit Secret
- `GUILD_ID`: optional numeric server ID for fast slash-command registration
- `PREFIX`: optional text-command prefix; defaults to `!`

Enable Message Content Intent and Server Members Intent in the Discord
Developer Portal before starting the bot.

## User preferences

- Keep the existing Python/nextcord stack.
- Do not add an unlimited DM or bulk-spam feature.