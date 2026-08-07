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
COOLDOWN_SECONDS = 30
MAX_CONTENT_LENGTH = 2_000
MAX_SEND_COUNT = 1

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


async def send_dm(
    sender_id: int,
    recipient: nextcord.User,
    content: str,
) -> str | None:
    """Send one non-pinging DM and return a user-facing error if it fails."""
    error = validate_dm_request(sender_id, recipient, content)
    if error:
        return error

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

    last_dm_at[sender_id] = time.monotonic()
    return None


async def resolve_recipient(
    selected_user: nextcord.User | None,
    user_id: str | None,
) -> tuple[nextcord.User | None, str | None]:
    """Resolve the selected user or an explicit Discord user ID."""
    if selected_user and user_id:
        return None, "Choose either a username or a user ID, not both."
    if user_id:
        if not user_id.isdigit():
            return None, "User ID must contain digits only."
        try:
            return await client.fetch_user(int(user_id)), None
        except nextcord.NotFound:
            return None, "No Discord user was found with that user ID."
        except nextcord.HTTPException:
            logger.exception("Discord user lookup failed")
            return None, "Discord could not look up that user right now."
    if selected_user:
        return selected_user, None
    return None, "Choose a username or provide a user ID."


@client.event
async def on_ready() -> None:
    logger.info("Logged in as %s (%s)", client.user, client.user.id)
    if GUILD_ID:
        logger.info("Slash commands are registered for guild %s", GUILD_ID)
    else:
        logger.info("Slash commands are global and may take time to appear")


@client.slash_command(
    name="dm",
    description="Send one direct message to a user",
    guild_ids=[GUILD_ID] if GUILD_ID else None,
)
async def dm_slash(
    interaction: nextcord.Interaction,
    message: str = nextcord.SlashOption(
        description="Message text (up to 2,000 characters)",
        max_length=MAX_CONTENT_LENGTH,
    ),
    times: int = nextcord.SlashOption(
        description="Number of messages (must be 1)",
        min_value=1,
        max_value=MAX_SEND_COUNT,
    ),
    username: nextcord.User | None = nextcord.SlashOption(
        description="Recipient username",
        required=False,
        default=None,
    ),
    user_id: str | None = nextcord.SlashOption(
        description="Recipient user ID (alternative to username)",
        required=False,
        default=None,
        min_length=17,
        max_length=20,
    ),
) -> None:
    if not interaction.guild or not isinstance(interaction.user, nextcord.Member):
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True,
        )
        return

    permission_message = permission_error(interaction.user)
    if permission_message:
        await interaction.response.send_message(permission_message, ephemeral=True)
        return

    if times != MAX_SEND_COUNT:
        await interaction.response.send_message(
            "Only one message per command is allowed.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    user, lookup_error = await resolve_recipient(username, user_id)
    if lookup_error or not user:
        await interaction.followup.send(lookup_error, ephemeral=True)
        return

    error = await send_dm(interaction.user.id, user, message)
    if error:
        await interaction.followup.send(error, ephemeral=True)
    else:
        await interaction.followup.send(f"DM sent to {user}.", ephemeral=True)


@client.command(name="dm")
@commands.guild_only()
@commands.has_guild_permissions(manage_messages=True)
async def dm_prefix(
    ctx: commands.Context,
    user: nextcord.User,
    *,
    content: str,
) -> None:
    error = await send_dm(ctx.author.id, user, content)
    await ctx.send(
        error or f"DM sent to {user}.",
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
    else:
        logger.error("Prefix command failed: %r", error)
        message = "The command failed unexpectedly. Check the bot logs."
    await ctx.send(message, delete_after=10)


if __name__ == "__main__":
    client.run(TOKEN)