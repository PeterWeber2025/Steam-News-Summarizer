# =============================================================================
# classifier.py
# Uses the LLM to classify a user message into one of three intent categories:
#
#   CHECK_FOLLOWED  — user wants news for all their followed games
#   ADD_GAME        — user wants to add a game to their followed list
#   QUICK_LOOKUP    — user wants news for a specific game, no list change
#
# Input:  raw user message string
# Output: one of the category strings defined in config.py
# =============================================================================

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

import config

# -----------------------------------------------------------------------------
# LLM Setup
# -----------------------------------------------------------------------------

_classifier_chain = None

_classifier_prompt = ChatPromptTemplate.from_template("""
You are a routing assistant for a Steam game news bot.
Classify the user's message into exactly ONE of the following categories.
Respond with ONLY the category name — nothing else, no punctuation, no explanation.

Categories:

CHECK_FOLLOWED
  The user wants to see recent news or updates for the games they are already
  following. They are not mentioning a specific game by name, or if they are,
  they are asking about games on their existing list.
  Examples:
  - "Any news for my games?"
  - "What's been happening with the games I follow?"
  - "Check my list"
  - "Any updates?"

ADD_GAME
  The user wants to add a specific game to their followed list so they can
  track it going forward. They are explicitly asking to follow, add, track,
  or subscribe to a game.
  Examples:
  - "Add Hollow Knight Silksong to my list"
  - "I want to follow Elden Ring"
  - "Start tracking Hades for me"
  - "Can you add Fallout New Vegas to my followed games?"

QUICK_LOOKUP
  The user wants to see news for a specific game right now, but is NOT asking
  to add it to their followed list. They just want a one-off check.
  Examples:
  - "What's new with Fallout New Vegas?"
  - "Any recent updates for Cyberpunk 2077?"
  - "Check the news for Stardew Valley"
  - "What has the Hades 2 team been saying lately?"

User message: {message}

Category:""")

def _get_classifier_chain():
    global _classifier_chain
    if _classifier_chain is None:
        _llm = ChatGoogleGenerativeAI(
            model=config.LLM_MODEL,
            temperature=config.CLASSIFIER_TEMPERATURE,
        )
        _classifier_chain = _classifier_prompt | _llm
    return _classifier_chain


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _extract_text(content) -> str:
    """
    Safely extract a plain string from an LLM response content field.
    Handles both simple string responses and list-of-block responses.
    Mirrors the extract_text helper from the lab.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
            elif hasattr(item, "text"):
                parts.append(item.text)
        return " ".join(parts)
    return str(content)


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def classify(message: str) -> str:
    """
    Classify a raw user message into an intent category.

    Args:
        message: The user's message as typed, before any parsing or extraction.

    Returns:
        One of the category strings from config.VALID_CATEGORIES:
        "CHECK_FOLLOWED", "ADD_GAME", or "QUICK_LOOKUP".
        Falls back to config.DEFAULT_CATEGORY if the LLM returns something
        unexpected.

    Example:
        >>> classify("Any news for my games?")
        "CHECK_FOLLOWED"

        >>> classify("Add Elden Ring to my list")
        "ADD_GAME"

        >>> classify("What's new with Stardew Valley?")
        "QUICK_LOOKUP"
    """
    result = _get_classifier_chain().invoke({"message": message})
    raw = _extract_text(result.content).strip().upper()

    # Match against valid categories — handles extra whitespace or punctuation
    for category in config.VALID_CATEGORIES:
        if category in raw:
            return category

    # Fallback if the LLM returned something unrecognized
    print(f"  ⚠️  Classifier returned unexpected value: '{raw}'. "
          f"Defaulting to {config.DEFAULT_CATEGORY}.")
    return config.DEFAULT_CATEGORY


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    test_messages = [
        # CHECK_FOLLOWED
        "Any news for my games?",
        "What's been happening with the games I follow?",
        "Check my list",
        "Any updates lately?",
        # ADD_GAME
        "Add Hollow Knight Silksong to my list",
        "I want to follow Elden Ring",
        "Can you start tracking Hades for me?",
        "Follow Fallout New Vegas",
        # QUICK_LOOKUP
        "What's new with Cyberpunk 2077?",
        "Any recent posts from the Stardew Valley dev?",
        "Check the news for Baldur's Gate 3",
        "What has the Hades 2 team been up to?",
    ]

    print("Classifier test:\n")
    for msg in test_messages:
        category = classify(msg)
        print(f"  [{category:>16}]  {msg}")
