# api/config.py
import os
import logging
from dotenv import load_dotenv

# Load .env file for local development (e.g., when running 'vercel dev')
load_dotenv() 

logger = logging.getLogger(__name__)

# --- Telegram Bot Configuration ---
TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# The full URL of *this* bot, e.g., "https://telegram-bot-delta-orpin.vercel.app"
VERCEL_URL = os.getenv("VERCEL_URL") 

# --- Grammar Service Configuration ---
# The full URL of your *other* project's API endpoint
# e.g., "https://grammar-fixer.vercel.app/api/correct"
GRAMMAR_ENDPOINT_URL = os.getenv("GRAMMAR_ENDPOINT_URL")

# --- Validation ---
missing_vars = []
if not TOKEN: missing_vars.append("TOKEN")
if not ADMIN_CHAT_ID: missing_vars.append("ADMIN_CHAT_ID")
if not VERCEL_URL: missing_vars.append("VERCEL_URL")
if not GRAMMAR_ENDPOINT_URL: missing_vars.append("GRAMMAR_ENDPOINT_URL")

if missing_vars:
    msg = f"Missing critical environment variables: {', '.join(missing_vars)}"
    logger.critical(msg)
    raise ValueError(msg)