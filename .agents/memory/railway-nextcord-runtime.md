---
name: Railway Nextcord runtime
description: Runtime compatibility constraints for deploying this Nextcord bot on Railway.
---

Use Python 3.12 for the Railway worker and keep `setuptools` below version 81.

**Why:** Python 3.13 removed `audioop`, which Nextcord imports during startup, and newer setuptools releases removed `pkg_resources`, which Nextcord 2.x also imports.

**How to apply:** Preserve the Python runtime pin and setuptools constraint when updating dependencies or rebuilding the Railway service. Upgrade Nextcord before reconsidering either constraint.