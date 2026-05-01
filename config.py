# =============================================================================
# config.py
# Central configuration for the Steam News Bot.
# All file paths, API settings, and LLM parameters live here.
# =============================================================================

# -----------------------------------------------------------------------------
# Environment — load .env file if present
# -----------------------------------------------------------------------------
# Create a .env file in the project root with:
#   GOOGLE_API_KEY=your_key_here
#
# The key is read automatically by langchain-google-genai from the environment.
# We just need to make sure it's loaded before any LLM objects are created.

from dotenv import load_dotenv
load_dotenv('key.env')  # does nothing on HF Spaces, but won't error
# GOOGLE_API_KEY needs to already be in os.environ via HF Secrets, if not probably an error

# -----------------------------------------------------------------------------
# LLM Settings (Google Gemini via LangChain)
# -----------------------------------------------------------------------------

# Model to use for classification, name extraction, and summarization
# gemini-2.5-flash is the current recommended fast model as of 2025
LLM_MODEL = "gemma-3-27b-it"

# Temperature for the classifier and name extractor — keep at 0 for
# deterministic routing decisions
CLASSIFIER_TEMPERATURE = 0

# Temperature for the summarizer — slight creativity is fine here
SUMMARIZER_TEMPERATURE = 0.3


# -----------------------------------------------------------------------------
# File Paths
# -----------------------------------------------------------------------------

# The full game catalog CSV — expects columns: AppID, Name, Release date
# (Release date is ignored at load time, only AppID and Name are used.)
# Place your dataset file here before running the bot.
CATALOG_CSV_PATH = "data/steam_catalog.csv"

# The user's persisted list of followed games: columns [game_name, app_id]
# This file is read and written by game_list.py.
FOLLOWED_GAMES_PATH = "data/followed_games.csv"

# Log file for conversations (optional, mirrors the lab's memory.csv)
MEMORY_LOG_PATH = "data/memory.csv"


# -----------------------------------------------------------------------------
# Steam News API Settings
# -----------------------------------------------------------------------------

# Base URL for the public Steam news endpoint (no API key required)
STEAM_NEWS_BASE_URL = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"

# Number of news posts to fetch per game
STEAM_NEWS_COUNT = 5

# Feed to pull from — filters to official developer announcements only.
# Use "steam_community_announcements" for dev posts.
# Use "steam_updates" for patch notes.
# Comma-separate to include both: "steam_community_announcements,steam_updates"
STEAM_NEWS_FEEDS = "steam_community_announcements"

# Max characters to return per post body.
# 0 = full content (includes raw BBCode/HTML tags — the LLM handles cleanup).
STEAM_NEWS_MAXLENGTH = 0

# Request timeout in seconds
STEAM_REQUEST_TIMEOUT = 10


# -----------------------------------------------------------------------------
# Classifier Categories
# -----------------------------------------------------------------------------
# These are the valid outputs from classifier.py.
# Defined here so router.py and classifier.py stay in sync
# without either one hardcoding strings independently.

CATEGORY_CHECK_FOLLOWED = "CHECK_FOLLOWED"
CATEGORY_ADD_GAME = "ADD_GAME"
CATEGORY_QUICK_LOOKUP = "QUICK_LOOKUP"

VALID_CATEGORIES = [
    CATEGORY_CHECK_FOLLOWED,
    CATEGORY_ADD_GAME,
    CATEGORY_QUICK_LOOKUP,
]

# Default fallback if the classifier returns something unexpected
DEFAULT_CATEGORY = CATEGORY_QUICK_LOOKUP


# -----------------------------------------------------------------------------
# Catalog Lookup Settings
# -----------------------------------------------------------------------------

# Column names as they appear in CATALOG_CSV_PATH.
# Matches the Kaggle dataset headers exactly: AppID, Name, Release date
# (Release date is ignored — only these two are read.)
CATALOG_NAME_COLUMN = "Name"
CATALOG_APPID_COLUMN = "AppID"

# Column names used in FOLLOWED_GAMES_PATH.
# This file is created by the bot, so we control the header names.
FOLLOWED_NAME_COLUMN = "game_name"
FOLLOWED_APPID_COLUMN = "app_id"
