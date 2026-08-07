---
name: Discord DM model
description: Product constraint for owner-authorized DM sending and message visibility.
---

The bot must use its own bot identity. It cannot log in as a personal Discord account, impersonate the owner, or create one shared private DM between two other users.

**Why:** Discord's bot and privacy model does not expose those capabilities.

**How to apply:** Authorize the owner with `OWNER_ID`, permit the owner to use the slash command in a DM with the bot, and deliver separate copies to the recipient and owner when both need to see the content.