# =============================================================================
# catalog_lookup.py
# Reads the Steam game catalog CSV and matches a user-provided game name
# to the closest entry using LLM-based fuzzy matching.
#
# Expected input:  a clean game name string (name extraction is router.py's job)
# Expected output: {"game_name": str, "app_id": int} or None
# =============================================================================

import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

import config

# -----------------------------------------------------------------------------
# Catalog Loading
# -----------------------------------------------------------------------------

# Module-level cache so we only read the CSV once per session.
_catalog_df = None


def _load_catalog() -> pd.DataFrame:
    """
    Load the game catalog CSV into a DataFrame, caching it after the first read.
    Only the Name and AppID columns are kept — Release date is dropped.
    """
    global _catalog_df

    if _catalog_df is not None:
        return _catalog_df

    if not os.path.exists(config.CATALOG_CSV_PATH):
        raise FileNotFoundError(
            f"Game catalog not found at '{config.CATALOG_CSV_PATH}'. "
            "Please place your steam_catalog.csv in the data/ folder."
        )

    _catalog_df = pd.read_csv(
        config.CATALOG_CSV_PATH,
        usecols=[config.CATALOG_NAME_COLUMN, config.CATALOG_APPID_COLUMN],
        encoding="utf-8",
    )

    # Drop rows with missing names or App IDs
    _catalog_df = _catalog_df.dropna(subset=[config.CATALOG_NAME_COLUMN, config.CATALOG_APPID_COLUMN])

    # Ensure AppID is stored as an integer
    _catalog_df[config.CATALOG_APPID_COLUMN] = _catalog_df[config.CATALOG_APPID_COLUMN].astype(int)

    return _catalog_df


# -----------------------------------------------------------------------------
# Candidate Filtering
# -----------------------------------------------------------------------------

def _get_candidates(game_name: str, df: pd.DataFrame, max_candidates: int = 20) -> list[str]:
    """
    Quickly narrow the 200k-row catalog down to a short list of plausible
    matches before sending anything to the LLM.

    Strategy:
    1. Look for entries where every word in the user's input appears in the
       catalog name (case-insensitive). This is fast and catches most cases.
    2. If that yields nothing, fall back to matching just the first word.
    3. Returns up to max_candidates game names as a plain list of strings.
    """
    name_series = df[config.CATALOG_NAME_COLUMN]
    words = game_name.lower().split()

    # All-words match
    mask = name_series.str.lower().apply(lambda n: all(w in n for w in words))
    results = df[mask][config.CATALOG_NAME_COLUMN].tolist()

    # First-word fallback
    if not results and words:
        mask = name_series.str.lower().str.contains(words[0], regex=False)
        results = df[mask][config.CATALOG_NAME_COLUMN].tolist()

    return results[:max_candidates]


# -----------------------------------------------------------------------------
# LLM Matching
# -----------------------------------------------------------------------------

_llm = ChatGoogleGenerativeAI(
    model=config.LLM_MODEL,
    temperature=config.CLASSIFIER_TEMPERATURE,
)

_match_prompt = ChatPromptTemplate.from_template("""
You are helping match a user's game name to the correct entry in a Steam game catalog.

User typed: "{user_input}"

Candidate matches from the catalog:
{candidates}

Instructions:
- Return ONLY the exact name from the candidates list that best matches what the user typed.
- Account for typos, abbreviations, missing subtitles, and partial names.
- If none of the candidates are a reasonable match, return exactly: NO_MATCH
- Do not return anything other than the exact candidate name or NO_MATCH.

Best match:""")

_match_chain = _match_prompt | _llm


def _llm_pick_best(user_input: str, candidates: list[str]) -> str | None:
    """
    Ask the LLM to pick the best match from a short candidate list.
    Returns the matched name string, or None if no match was found.
    """
    candidates_text = "\n".join(f"- {c}" for c in candidates)
    result = _match_chain.invoke({
        "user_input": user_input,
        "candidates": candidates_text,
    })

    picked = result.content.strip()

    if picked == "NO_MATCH" or not picked:
        return None

    return picked


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def find_game(game_name: str) -> dict | None:
    """
    Match a clean game name string to an entry in the Steam catalog.

    Args:
        game_name: A game name as provided by the user, after extraction
                   by the router. E.g. "Hollow Knight Silksong" or
                   "fallout new vegas".

    Returns:
        A dict with keys "game_name" (str) and "app_id" (int),
        or None if no confident match could be found.

    Example:
        >>> find_game("Hollow Knight Silksong")
        {"game_name": "Hollow Knight: Silksong", "app_id": 1030300}

        >>> find_game("xyzzy game that does not exist")
        None
    """
    df = _load_catalog()

    # Step 1: Fast keyword filter to get a short candidate list
    candidates = _get_candidates(game_name, df)

    if not candidates:
        return None

    # Step 2: LLM picks the best match from the candidates
    best_name = _llm_pick_best(game_name, candidates)

    if best_name is None:
        return None

    # Step 3: Look up the App ID for the matched name
    row = df[df[config.CATALOG_NAME_COLUMN] == best_name]

    if row.empty:
        return None

    app_id = int(row.iloc[0][config.CATALOG_APPID_COLUMN])

    return {
        "game_name": best_name,
        "app_id": app_id,
    }


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    test_inputs = [
        "Hollow Knight Silksong",
        "fallout new vegas",
        "hades",
        "elden ring",
        "this game definitely does not exist xyz",
    ]

    for name in test_inputs:
        result = find_game(name)
        if result:
            print(f"  ✅ '{name}' → {result['game_name']} (AppID: {result['app_id']})")
        else:
            print(f"  ❌ '{name}' → No match found")
