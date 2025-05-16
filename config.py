#!/usr/bin/env python3
"""Configuration file for Discord leveling bot."""

# File paths
TOKEN_FILE = "token"
DATABASE = "persist.db"
MINUTE_TIME = 5


GENERAL = 293168705058111489
TRACKED_GUILD = 148831815984087041

# Load token from file at import time
with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()
