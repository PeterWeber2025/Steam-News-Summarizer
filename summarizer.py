# =============================================================================
# summarizer.py
# Takes raw Steam news posts for a single game and produces a concise,
# human-readable summary using the LLM.
#
# Input:  game name (str) + list of post dicts from steam_api.py
# Output: a formatted summary string ready to display to the user
# =============================================================================

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

import config

# -----------------------------------------------------------------------------
# LLM Setup
# -----------------------------------------------------------------------------

_llm = ChatGoogleGenerativeAI(
    model=config.LLM_MODEL,
    temperature=config.SUMMARIZER_TEMPERATURE,
)

_summarize_prompt = ChatPromptTemplate.from_template("""
You are a gaming news assistant summarizing official developer posts from Steam.

Game: {game_name}

Recent developer posts:
{posts_text}

Instructions:
- Write a concise summary of what the developers have been posting about.
- Focus on the most important updates: new content, patches, fixes, events, or announcements.
- If multiple posts cover the same topic, consolidate them into one point.
- Strip out any BBCode or HTML formatting tags (like [b], [url], <br>, etc.) from the content.
- Use plain, readable sentences. Bullet points are fine for distinct updates.
- Include the post date next to each point where relevant, in parentheses.
- If the posts contain nothing meaningful (e.g. only social media links or empty content), say so briefly.
- Do not editorialize or add opinions — stick to what the developers actually said.
- Keep the total summary under 200 words.

Summary:""")

_summarize_chain = _summarize_prompt | _llm


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _format_posts_for_prompt(posts: list[dict]) -> str:
    """
    Convert a list of post dicts into a plain text block suitable for
    inclusion in the summarization prompt.

    Each post is formatted as:
        [DATE] TITLE
        Author: AUTHOR
        CONTENTS
        ---
    """
    sections = []

    for post in posts:
        author_line = f"Author: {post['author']}" if post["author"] else ""
        parts = [
            f"[{post['date']}] {post['title']}",
            author_line,
            post["contents"],
        ]
        # Drop empty lines (e.g. missing author)
        section = "\n".join(p for p in parts if p)
        sections.append(section)

    return "\n---\n".join(sections)


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def summarize_game_news(game_name: str, posts: list[dict]) -> str:
    """
    Summarize a list of developer posts for a single game.

    Args:
        game_name: The canonical name of the game, used in the prompt and
                   in the returned header so the output is self-labelled.
        posts:     A list of post dicts as returned by steam_api.py.
                   Each dict should have: title, date, author, contents.

    Returns:
        A formatted string containing a header and the LLM-generated summary.
        If no posts were provided, returns a short "no news" message instead
        of making an LLM call.

    Example output:
        ════════════════════════════════════════
        🎮 Hades
        ════════════════════════════════════════
        • Patch 1.3 released (2024-11-01): Fixed a bug with the Skelly room...
        • Seasonal event announced (2024-10-28): The Winter Solstice event...
    """
    header = f"\n{'═' * 40}\n🎮  {game_name}\n{'═' * 40}"

    if not posts:
        return f"{header}\nNo recent developer posts found."

    posts_text = _format_posts_for_prompt(posts)

    result = _llm.invoke(
        _summarize_chain.invoke({
            "game_name": game_name,
            "posts_text": posts_text,
        }).content
    )

    # _summarize_chain already returns an AIMessage — extract text
    summary_text = result.content.strip()

    return f"{header}\n{summary_text}"


def summarize_all_games(news_by_app_id: dict[int, list[dict]], games: list[dict]) -> str:
    """
    Summarize news for multiple games and stitch the results together.

    Args:
        news_by_app_id: Dict mapping app_id → list of posts, as returned
                        by steam_api.get_news_for_games().
        games:          List of game dicts with "game_name" and "app_id" keys,
                        used to look up the display name for each App ID.

    Returns:
        A single string with one summary block per game, in the same order
        as the games list.

    Example:
        >>> output = summarize_all_games(news_by_app_id, followed_games)
        >>> print(output)
    """
    # Build a quick app_id → game_name lookup
    name_lookup = {g["app_id"]: g["game_name"] for g in games}

    summaries = []
    for app_id, posts in news_by_app_id.items():
        game_name = name_lookup.get(app_id, f"App {app_id}")
        print(f"  ✍️  Summarizing {game_name}...")
        summaries.append(summarize_game_news(game_name, posts))

    return "\n".join(summaries)


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    from steam_api import get_news_for_game

    TEST_GAME = {"game_name": "Hades", "app_id": 1145360}

    print(f"Fetching posts for {TEST_GAME['game_name']}...\n")
    posts = get_news_for_game(TEST_GAME["app_id"])

    print(f"Got {len(posts)} post(s). Summarizing...\n")
    summary = summarize_game_news(TEST_GAME["game_name"], posts)
    print(summary)
