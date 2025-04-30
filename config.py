#!/usr/bin/env python3
"""Configuration file for Discord leveling bot."""

# File paths
TOKEN_FILE = "token"
DATABASE = "persist.db"
MINUTE_TIME = 5

# Load token from file at import time
with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()
