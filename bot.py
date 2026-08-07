"""A small, rate-limited Discord DM utility built with nextcord.

The bot intentionally sends one DM per command.  This keeps the command useful
for moderation/support workflows without providing an unlimited DM spam loop.
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict

import nextcord
from dotenv import load_dotenv
from nextcord.ext import commands


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord-dm-bot")


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.lower().startswith(("put your ", "your ")):
        raise RuntimeError(
            f"Missing {name}. Add it to Replit Secrets or your local .env file."
        )
    return value


def optional_int_env(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    if not value or value.lower() in {"exampleid", "your_guild_id"}:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a whole number.") from error


TOKEN = required_env("TOKEN")
PREFIX = os.getenv("PREFIX", "!").strip() or "!"
GUILD_ID = optional_int_env("GUILD_ID") or optional_int_env("GUILDID")
OWNER_ID = optional_int_env("OWNER_ID")
COOLDOWN_SECONDS = 30
MAX_CONTENT_LENGTH = 2_000
MAX_SEND_COUNT = 10000

intents = nextcord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

client = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
)

# A per-user cooldown prevents accidental rapid repeats without blocking the
# rest of the server from using the bot.
last_dm_at: defaultdict[int, float] = defaultdict(lambda: 0.0)


def permission_error(member: nextcord.Member) -> str | None:
    if not member.guild_permissions.manage_messages:
        return "You need the Manage Messages permission to use this command."
    return None


def owner_authorized(user: nextcord.User | nextcord.Member) -> bool:
    return OWNER_ID is not None and user.id == OWNER_ID


def validate_dm_request(
    sender_id: int,
    recipient: nextcord.User,
    content: str,
) -> str | None:
    remaining = COOLDOWN_SECONDS - (time.monotonic() - last_dm_at[sender_id])
    if remaining > 0:
        return f"Please wait {remaining:.0f}s before sending another DM."
    if client.user and recipient.id == client.user.id:
        return "Please choose a human recipient."
    if not content.strip():
        return "Message content cannot be empty."
    if len(content) > MAX_CONTENT_LENGTH:
        return f"Message content must be {MAX_CONTENT_LENGTH} characters or fewer."
    return None


async def deliver_dm(
    recipient: nextcord.User,
    content: str,
) -> str | None:
    try:
        await recipient.send(
            content,
            allowed_mentions=nextcord.AllowedMentions.none(),
        )
    except nextcord.Forbidden:
        return "Discord rejected the DM. The recipient may have DMs disabled or blocked the bot."
    except nextcord.NotFound:
        return "That Discord user no longer exists."
    except nextcord.HTTPException:
        logger.exception("Discord rejected a DM request")
        return "Discord could not deliver the DM right now. Please try again later."


async def send_dm(
    sender_id: int,
    recipient: nextcord.User,
    content: str,
) -> str | None:
    """Validate and send one non-pinging DM."""
    error = validate_dm_request(sender_id, recipient, content)
    if error:
        return error
    error = await deliver_dm(recipient, content)
    if error:
        return error
    last_dm_at[sender_id] = time.monotonic()
    return None


async def send_dm_with_owner_copy(
    sender_id: int,
    recipient: nextcord.User,
    content: str,
) -> str | None:
    """Send to the recipient and, when configured, send the owner a copy."""
    error = validate_dm_request(sender_id, recipient, content)
    if error:
        return error

    error = await deliver_dm(recipient, content)
    if error:
        return error
    last_dm_at[sender_id] = time.monotonic()

    if OWNER_ID and OWNER_ID != recipient.id:
        try:
            owner = client.get_user(OWNER_ID) or await client.fetch_user(OWNER_ID)
            owner_error = await deliver_dm(owner, content)
            if owner_error:
                return f"Message sent to {recipient}, but the owner copy failed: {owner_error}"
        except nextcord.HTTPException:
            logger.exception("Could not look up the configured bot owner")
            return f"Message sent to {recipient}, but the owner copy could not be delivered."
    return None


@client.event
async def on_ready() -> None:
    logger.info("Logged in as %s (%s)", client.user, client.user.id)
    logger.info("The /dm slash command is global and enabled in direct messages")


@client.slash_command(
    name="dm",
    description="Send one direct message to a user",
    # A global command is required so the owner can use it in a DM with the bot.
    # It may take up to an hour to appear after the first deployment.
    guild_ids=None,
    dm_permission=True,
    force_global=True,
)
async def dm_slash(
    interaction: nextcord.Interaction,
    message: str = nextcord.SlashOption(
        description="Message text (up to 2,000 characters)",
        max_length=MAX_CONTENT_LENGTH,
    ),
    times: int = nextcord.SlashOption(
        description="Number of messages (1 to 10000)",
        min_value=1,
        max_value=MAX_SEND_COUNT,
    ),
    username: nextcord.User = nextcord.SlashOption(
        description="Recipient username",
        required=True,
    ),
) -> None:
    if not interaction.guild:
        if not owner_authorized(interaction.user):
            await interaction.response.send_message(
                "Only the configured bot owner can use this command in DMs.",
                ephemeral=True,
            )
            return
    elif not isinstance(interaction.user, nextcord.Member):
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True,
        )
        return

    permission_message = (
        None
        if owner_authorized(interaction.user)
        else permission_error(interaction.user)
    )
    if permission_message:
        await interaction.response.send_message(permission_message, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    error = await send_dm_with_owner_copy(interaction.user.id, username, message)
    if error:
        await interaction.followup.send(error, ephemeral=True)
    else:
        copy_note = " A copy was sent to the bot owner." if OWNER_ID else ""
        await interaction.followup.send(
            f"DM sent to {username}.{copy_note}",
            ephemeral=True,
        )


@client.command(name="dm")
@commands.check(
    lambda ctx: owner_authorized(ctx.author)
    or (ctx.guild is not None and ctx.author.guild_permissions.manage_messages)
)
async def dm_prefix(
    ctx: commands.Context,
    user: nextcord.User,
    *,
    content: str,
) -> None:
    error = await send_dm_with_owner_copy(ctx.author.id, user, content)
    await ctx.send(
        error or f"DM sent to {user}."
        + (" A copy was sent to the bot owner." if OWNER_ID else ""),
        allowed_mentions=nextcord.AllowedMentions.none(),
        delete_after=10,
    )


@dm_prefix.error
async def dm_prefix_error(ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.MissingPermissions):
        message = "You need the Manage Messages permission to use this command."
    elif isinstance(error, commands.NoPrivateMessage):
        message = "This command can only be used inside a server."
    elif isinstance(error, commands.MissingRequiredArgument):
        message = f"Usage: `{PREFIX}dm @user your message here`"
    elif isinstance(error, commands.BadArgument):
        message = "I could not find that Discord user. Mention them or use their user ID."
    elif isinstance(error, commands.CheckFailure):
        message = "Only the bot owner or a member with Manage Messages can use this command."
    else:
        logger.error("Prefix command failed: %r", error)
        message = "The command failed unexpectedly. Check the bot logs."
    await ctx.send(message, delete_after=10)


if __name__ == "__main__":
    client.run(TOKEN)
