# =============================================================================
# router.py
# Main orchestration logic for the Steam News Bot.
# Classifies the user's message, extracts game names where needed,
# and routes to the correct combination of modules.
#
# This is the single entry point that app.py calls. Everything else is
# an implementation detail hidden behind handle_message().
#
# Pipeline:
#   User message
#     → classify()               — what does the user want?
#     → extract_game_name()      — which game are they asking about? (if needed)
#     → catalog_lookup.find_game() — resolve name to App ID
#     → steam_api.get_news_*()   — fetch posts from Steam
#     → summarizer.summarize_*() — generate readable summary
#     → return response string
# =============================================================================

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

import config
from modules import classifier
from modules import catalog_lookup
from modules import game_list
from modules import steam_api
from modules import summarizer

# -----------------------------------------------------------------------------
# Game Name Extractor
# -----------------------------------------------------------------------------
# Runs before catalog_lookup for ADD_GAME and QUICK_LOOKUP branches.
# Takes the raw user message and returns just the game name as a clean string.

_extract_chain = None

_extract_prompt = ChatPromptTemplate.from_template("""
You are helping extract a game title from a user's message.

User message: "{message}"

Instructions:
- Return ONLY the game title the user is referring to.
- Do not include any extra words, punctuation, or explanation.
- Preserve the original capitalisation and spelling as the user typed it.
- If you cannot identify a game title, return exactly: NO_GAME

Game title:""")


def _get_extract_chain():
    global _extract_chain
    if _extract_chain is None:
        _llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            temperature=config.CLASSIFIER_TEMPERATURE,
        )
        _extract_chain = _extract_prompt | _llm
    return _extract_chain


def _extract_game_name(message: str) -> str | None:
    """
    Extract a game name from a raw user message.

    Returns the extracted name as a string, or None if no game could
    be identified.

    Examples:
        "Add Hollow Knight Silksong to my list" → "Hollow Knight Silksong"
        "What's new with Fallout New Vegas?"    → "Fallout New Vegas"
        "Any updates?"                          → None
    """
    result = _get_extract_chain().invoke({"message": message})
    extracted = result.content.strip()

    if extracted == "NO_GAME" or not extracted:
        return None

    return extracted


# -----------------------------------------------------------------------------
# Branch Handlers
# -----------------------------------------------------------------------------

def _handle_check_followed() -> str:
    """
    CHECK_FOLLOWED branch.
    Load the followed list, fetch news for every game, summarize each one.
    """
    games = game_list.get_followed_games()

    if not games:
        return (
            "You are not following any games yet.\n"
            "Try: \"Add Hades to my list\" or \"What's new with Hollow Knight?\""
        )

    print(f"  📋 Checking news for {len(games)} followed game(s)...")
    news_by_app_id = steam_api.get_news_for_games(games)
    return summarizer.summarize_all_games(news_by_app_id, games)


def _handle_add_game(message: str) -> str:
    """
    ADD_GAME branch.
    Extract the game name, find it in the catalog, add it to the followed list.
    """
    # Step 1: Extract the game name from the message
    game_name = _extract_game_name(message)

    if not game_name:
        return (
            "I couldn't identify a game name in your message. "
            "Try: \"Add Hollow Knight Silksong to my list.\""
        )

    print(f"  🔍 Extracted game name: '{game_name}'")

    # Step 2: Look up the game in the catalog
    match = catalog_lookup.find_game(game_name)

    if not match:
        return (
            f"I couldn't find \"{game_name}\" in the Steam catalog. "
            "Check the spelling and try again."
        )

    print(f"  ✅ Matched: {match['game_name']} (AppID: {match['app_id']})")

    # Step 3: Check if already followed
    if game_list.is_followed(match["app_id"]):
        return f"You are already following **{match['game_name']}**."

    # Step 4: Add to the followed list
    game_list.add_game(match["game_name"], match["app_id"])

    return (
        f"Added **{match['game_name']}** (AppID: {match['app_id']}) "
        f"to your followed games. 🎮"
    )


def _handle_quick_lookup(message: str) -> str:
    """
    QUICK_LOOKUP branch.
    Extract the game name, find it in the catalog, fetch and summarize news.
    Does not touch the followed list.
    """
    # Step 1: Extract the game name from the message
    game_name = _extract_game_name(message)

    if not game_name:
        return (
            "I couldn't identify a game name in your message. "
            "Try: \"What's new with Hades?\""
        )

    print(f"  🔍 Extracted game name: '{game_name}'")

    # Step 2: Look up in the catalog
    match = catalog_lookup.find_game(game_name)

    if not match:
        return (
            f"I couldn't find \"{game_name}\" in the Steam catalog. "
            "Check the spelling and try again."
        )

    print(f"  ✅ Matched: {match['game_name']} (AppID: {match['app_id']})")

    # Step 3: Fetch news from Steam
    print(f"  📡 Fetching news for {match['game_name']}...")
    posts = steam_api.get_news_for_game(match["app_id"])

    # Step 4: Summarize
    print(f"  ✍️  Summarizing...")
    return summarizer.summarize_game_news(match["game_name"], posts)


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def handle_message(message: str) -> str:
    """
    Main entry point. Takes a raw user message and returns a response string.

    This is the only function app.py needs to call.

    Args:
        message: The user's message as typed into the Gradio chat interface.

    Returns:
        A response string ready to display to the user.
    """
    print(f"\n{'─' * 50}")
    print(f"  💬 User: {message}")

    # Step 1: Classify the message
    category = classifier.classify(message)
    print(f"  🏷️  Category: {category}")

    # Step 2: Route to the correct handler
    if category == config.CATEGORY_CHECK_FOLLOWED:
        response = _handle_check_followed()

    elif category == config.CATEGORY_ADD_GAME:
        response = _handle_add_game(message)

    elif category == config.CATEGORY_QUICK_LOOKUP:
        response = _handle_quick_lookup(message)

    else:
        # Should never happen given the fallback in classifier.py,
        # but handle it gracefully just in case.
        response = (
            "I'm not sure what you're asking. Try one of these:\n"
            "- \"Any news for my games?\"\n"
            "- \"Add Hades to my list\"\n"
            "- \"What's new with Elden Ring?\""
        )

    print(f"{'─' * 50}\n")
    return response


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    test_messages = [
        "Add Hades to my followed list",
        "What's new with Hollow Knight?",
        "Any updates for my games?",
        "Add Elden Ring",
        "Check the latest news for Stardew Valley",
        "Any news?",
    ]

    for msg in test_messages:
        print(f"\n{'═' * 50}")
        response = handle_message(msg)
        print(f"\n🤖 Response:\n{response}")
