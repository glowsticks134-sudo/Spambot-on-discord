# Project overview

This is a Python `nextcord` Discord bot. The supported commands are `/dm` and
`<prefix>dm`; each sends one non-pinging direct message to a selected user.
Commands are restricted to members with the Manage Messages permission and
include a per-user cooldown.

## Deployment on Railway

The project uses Python 3.12 and the dependencies in `requirements.txt`.
`runtime.txt` pins Railway to Python 3.12.11 because Python 3.13 removed the
standard-library `audioop` module that Nextcord still imports at startup.
`requirements.txt` also pins setuptools below 81 because Nextcord 2.x imports
the `pkg_resources` compatibility module.
Railway runs the long-lived worker with the included `Procfile`:

```text
worker: python bot.py
```

Required configuration:

- `TOKEN`: Discord bot token, stored as a Railway service variable
- `GUILD_ID`: optional numeric server ID for fast slash-command registration
- `OWNER_ID`: your Discord account ID; authorizes your account in DMs and
  receives a copy of messages sent through the bot
- `PREFIX`: optional text-command prefix; defaults to `!`

Enable Message Content Intent and Server Members Intent in the Discord
Developer Portal before deploying. This bot does not expose an HTTP port; a
healthy Railway deployment is confirmed by the startup log showing a
successful Discord login.

The Replit `Discord bot` console workflow is available for local checks only;
Railway is the production host.

## User preferences

- Keep the existing Python/nextcord stack.
- Do not add an unlimited DM or bulk-spam feature.