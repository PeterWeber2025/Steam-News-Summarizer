# =============================================================================
# game_list.py
# All read/write operations for the user's persisted followed-games list.
# No LLM calls live here — this is purely data management.
#
# The followed games file is a CSV with two columns: game_name, app_id
# It is created automatically on first add if it doesn't exist yet.
# =============================================================================

import os
import pandas as pd

import config

# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------

def _load() -> pd.DataFrame:
    """
    Load the followed games CSV into a DataFrame.
    If the file doesn't exist yet, return an empty DataFrame with the
    correct columns — the file will be created on the first write.
    """
    if not os.path.exists(config.FOLLOWED_GAMES_PATH):
        return pd.DataFrame(columns=[
            config.FOLLOWED_NAME_COLUMN,
            config.FOLLOWED_APPID_COLUMN,
        ])

    return pd.read_csv(
        config.FOLLOWED_GAMES_PATH,
        encoding="utf-8",
        dtype={config.FOLLOWED_APPID_COLUMN: int},
    )


def _save(df: pd.DataFrame) -> None:
    """
    Write the DataFrame back to the followed games CSV.
    Creates the data/ directory if it doesn't exist yet.
    """
    os.makedirs(os.path.dirname(config.FOLLOWED_GAMES_PATH), exist_ok=True)
    df.to_csv(config.FOLLOWED_GAMES_PATH, index=False, encoding="utf-8")


# -----------------------------------------------------------------------------
# Public Interface
# -----------------------------------------------------------------------------

def get_followed_games() -> list[dict]:
    """
    Return the full list of followed games.

    Returns:
        A list of dicts, each with keys "game_name" (str) and "app_id" (int).
        Returns an empty list if no games are being followed yet.

    Example:
        >>> get_followed_games()
        [
            {"game_name": "Hades", "app_id": 1145360},
            {"game_name": "Hollow Knight: Silksong", "app_id": 1030300},
        ]
    """
    df = _load()
    return df.to_dict(orient="records")


def add_game(game_name: str, app_id: int) -> bool:
    """
    Add a game to the followed list. Does nothing if the App ID is already
    present (prevents duplicates even if the user types the name differently).

    Args:
        game_name: The canonical game name from the catalog lookup.
        app_id:    The Steam App ID for the game.

    Returns:
        True if the game was added, False if it was already on the list.

    Example:
        >>> add_game("Hades", 1145360)
        True
        >>> add_game("Hades", 1145360)  # second call — already followed
        False
    """
    df = _load()

    already_followed = app_id in df[config.FOLLOWED_APPID_COLUMN].values

    if already_followed:
        return False

    new_row = pd.DataFrame([{
        config.FOLLOWED_NAME_COLUMN: game_name,
        config.FOLLOWED_APPID_COLUMN: app_id,
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    _save(df)
    return True


def remove_game(app_id: int) -> bool:
    """
    Remove a game from the followed list by App ID.

    Args:
        app_id: The Steam App ID of the game to remove.

    Returns:
        True if the game was found and removed, False if it wasn't on the list.

    Example:
        >>> remove_game(1145360)
        True
        >>> remove_game(1145360)  # already removed
        False
    """
    df = _load()

    mask = df[config.FOLLOWED_APPID_COLUMN] == app_id
    if not mask.any():
        return False

    df = df[~mask].reset_index(drop=True)
    _save(df)
    return True


def is_followed(app_id: int) -> bool:
    """
    Check whether a game is already on the followed list.

    Args:
        app_id: The Steam App ID to check.

    Returns:
        True if the game is followed, False otherwise.
    """
    df = _load()
    return app_id in df[config.FOLLOWED_APPID_COLUMN].values


# -----------------------------------------------------------------------------
# Manual Test
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("--- Initial list ---")
    print(get_followed_games())

    print("\n--- Adding Hades (1145360) ---")
    print("Added:", add_game("Hades", 1145360))

    print("\n--- Adding Hollow Knight: Silksong (1030300) ---")
    print("Added:", add_game("Hollow Knight: Silksong", 1030300))

    print("\n--- Adding Hades again (should be False) ---")
    print("Added:", add_game("Hades", 1145360))

    print("\n--- Current list ---")
    for game in get_followed_games():
        print(f"  {game['game_name']} (AppID: {game['app_id']})")

    print("\n--- is_followed(1145360) ---")
    print(is_followed(1145360))

    print("\n--- Removing Hades (1145360) ---")
    print("Removed:", remove_game(1145360))

    print("\n--- Removing Hades again (should be False) ---")
    print("Removed:", remove_game(1145360))

    print("\n--- Final list ---")
    print(get_followed_games())
