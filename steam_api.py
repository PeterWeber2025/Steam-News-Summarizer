# =============================================================================
# steam_api.py
# Fetches developer news posts from the Steam News API for a given App ID.
# No LLM calls here — raw post data is returned as-is for summarizer.py
# to process.
#
# API endpoint: GET https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/
# No API key required.
# =============================================================================

import requests
from datetime import datetime

import config

# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

# Each returned post is a plain dict with these keys:
#
#   gid        (str)  — unique ID for the post
#   title      (str)  — post title
#   url        (str)  — link to the full post on Steam
#   author     (str)  — who posted it (may be empty string)
#   contents   (str)  — full post body, may contain BBCode/HTML tags
#   date       (str)  — human-readable date, e.g. "2024-11-03"
#   feedname   (str)  — raw feed name, e.g. "steam_community_announcements"


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _parse_post(item: dict) -> dict:
    """
    Normalize a raw news item from the Steam API response into a clean dict.
    Converts the Unix timestamp to a readable date string.
    """
    timestamp = item.get("date", 0)
    try:
        readable_date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
    except (OSError, OverflowError, ValueError):
        readable_date = "Unknown date"

    return {
        "gid":      item.get("gid", ""),
        "title":    item.get("title", "Untitled"),
        "url":      item.get("url", ""),
        "author":   item.get("author", ""),
        "contents": item.get("contents", ""),
        "date":     readable_date,
        "feedname": item.get("feedname", ""),
    }


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def get_news_for_game(app_id: int) -> list[dict]:
    """
    Fetch recent developer posts for a single game by App ID.

    Calls the Steam News API with the feed and count settings from config.py.
    Returns a list of post dicts (may be empty if the game has no recent posts
    or if the API call fails).

    Args:
        app_id: The Steam App ID of the game.

    Returns:
        A list of post dicts, each with keys:
        gid, title, url, author, contents, date, feedname.
        Returns an empty list on any error rather than raising, so the
        caller can continue processing other games.

    Example:
        >>> posts = get_news_for_game(1145360)  # Hades
        >>> for post in posts:
        ...     print(post["date"], post["title"])
    """
    params = {
        "appid":     app_id,
        "count":     config.STEAM_NEWS_COUNT,
        "maxlength": config.STEAM_NEWS_MAXLENGTH,
        "feeds":     config.STEAM_NEWS_FEEDS,
        "format":    "json",
    }

    try:
        response = requests.get(
            config.STEAM_NEWS_BASE_URL,
            params=params,
            timeout=config.STEAM_REQUEST_TIMEOUT,
        )
        response.raise_for_status()

    except requests.exceptions.Timeout:
        print(f"  ⚠️  Timeout fetching news for AppID {app_id}")
        return []

    except requests.exceptions.HTTPError as e:
        print(f"  ⚠️  HTTP error fetching news for AppID {app_id}: {e}")
        return []

    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  Request error fetching news for AppID {app_id}: {e}")
        return []

    data = response.json()

    # The API wraps results in appnews > newsitems
    try:
        raw_items = data["appnews"]["newsitems"]
    except (KeyError, TypeError):
        # Game exists but has no news, or unexpected response shape
        return []

    return [_parse_post(item) for item in raw_items]


def get_news_for_games(games: list[dict]) -> dict[int, list[dict]]:
    """
    Fetch news for multiple games, returning a dict keyed by App ID.

    Args:
        games: A list of game dicts, each with at minimum "app_id" and
               "game_name" keys — the same shape returned by game_list.py
               and catalog_lookup.py.

    Returns:
        A dict mapping app_id (int) → list of post dicts.
        Games with no posts still get an entry with an empty list, so
        the caller always knows which games were checked.

    Example:
        >>> games = [
        ...     {"game_name": "Hades", "app_id": 1145360},
        ...     {"game_name": "Hollow Knight: Silksong", "app_id": 1030300},
        ... ]
        >>> results = get_news_for_games(games)
        >>> results[1145360]  # list of posts for Hades
    """
    results = {}

    for game in games:
        app_id = game["app_id"]
        game_name = game["game_name"]
        print(f"  📡 Fetching news for {game_name} (AppID: {app_id})...")
        results[app_id] = get_news_for_game(app_id)

    return results


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Hades — a game that reliably has developer posts
    TEST_APP_ID = 1145360
    TEST_GAME_NAME = "Hades"

    print(f"Fetching news for {TEST_GAME_NAME} (AppID: {TEST_APP_ID})...\n")
    posts = get_news_for_game(TEST_APP_ID)

    if not posts:
        print("No posts returned. Check your feed name or App ID.")
    else:
        for i, post in enumerate(posts, 1):
            print(f"--- Post {i} ---")
            print(f"  Title:  {post['title']}")
            print(f"  Date:   {post['date']}")
            print(f"  Author: {post['author']}")
            print(f"  URL:    {post['url']}")
            print(f"  Feed:   {post['feedname']}")
            print(f"  Body preview: {post['contents'][:200]}...")
            print()
