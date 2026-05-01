# =============================================================================
# app.py
# Gradio UI for the Steam News Bot.
# This is the only file you run: `python app.py`
#
# All logic lives in router.py — this file is purely the interface layer.
# Uses gr.Blocks with gr.ChatInterface for Gradio 6.x compatibility.
# =============================================================================

import gradio as gr
from modules import game_list
from modules import router

# -----------------------------------------------------------------------------
# UI Helper
# -----------------------------------------------------------------------------

def _get_followed_list_text() -> str:
    """
    Build a display string of currently followed games for the sidebar panel.
    Called on load and after every message that might change the list.
    """
    games = game_list.get_followed_games()
    if not games:
        return "*(none yet)*"
    return "\n".join(f"• {g['game_name']}" for g in games)


# -----------------------------------------------------------------------------
# Chat Handler
# -----------------------------------------------------------------------------

import os

def chat(message: str, history: list) -> tuple[str, str]:
    if not os.getenv("GOOGLE_API_KEY"):
        return (
            "⚠️ No API key configured. If you're running this on Hugging Face Spaces, "
            "go to Settings → Variables and Secrets and add your GOOGLE_API_KEY.",
            _get_followed_list_text()
        )
    response = router.handle_message(message)
    return response, _get_followed_list_text()


# -----------------------------------------------------------------------------
# Styling
# -----------------------------------------------------------------------------

CSS = """
    .gradio-container {
        background-color: #1a1b1e !important;
        color: #e8e8e8 !important;
    }
    #header {
        text-align: center;
        padding: 24px 0 8px 0;
        border-bottom: 1px solid #2e2f33;
        margin-bottom: 16px;
    }
    #header h1 {
        font-size: 2.4em;
        font-weight: 700;
        letter-spacing: 0.04em;
        color: #e8e8e8;
        margin: 0;
    }
    #header h1 span {
        color: #e87b35;
    }
    #header p {
        color: #888;
        margin: 6px 0 0 0;
        font-size: 0.95em;
    }
    #followed-panel {
        background-color: #222326;
        border: 1px solid #2e2f33;
        border-radius: 8px;
        padding: 14px 16px;
        min-height: 100px;
        color: #e8e8e8 !important;
    }
    #followed-panel p, #followed-panel li {
        color: #e8e8e8 !important;
    }
    .examples-holder button, .examples button {
        background-color: #2e2f33 !important;
        color: #e8e8e8 !important;
        border: 1px solid #444 !important;
    }
    .examples-holder button:hover, .examples button:hover {
        background-color: #3a3b3f !important;
    }
    #followed-label {
        font-size: 0.75em;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #e87b35;
        font-weight: 600;
        margin-bottom: 8px;
    }
    #send-btn {
        background-color: #e87b35 !important;
        color: #fff !important;
        border: none !important;
        font-weight: 600 !important;
    }
    #send-btn:hover {
        background-color: #cf6a27 !important;
    }
"""

THEME = gr.themes.Base(
    primary_hue="orange",
    neutral_hue="zinc",
    font=gr.themes.GoogleFont("Rajdhani"),
)


# -----------------------------------------------------------------------------
# Gradio Interface
# -----------------------------------------------------------------------------

with gr.Blocks(title="Steam News Bot") as demo:

    gr.HTML("""
        <div id="header">
            <h1>🎮 Steam <span>News</span> Bot</h1>
            <p>Track developer posts across your followed games — no manual checking required.</p>
        </div>
    """)

    # Declare before ChatInterface so it can be referenced in additional_outputs,
    # but defer rendering until the right column with .render()
    followed_display = gr.Markdown(
        value=_get_followed_list_text(),
        elem_id="followed-panel",
        render=False,
    )

    with gr.Row():

        # Left — chat interface
        with gr.Column(scale=3):
            chat_interface = gr.ChatInterface(
                fn=chat,
                additional_outputs=[followed_display],
                examples=[
                    "Any news for my games?",
                    "Add Hades to my followed list",
                    "Add Hollow Knight: Silksong to my list",
                    "What's new with Stardew Valley?",
                    "Any recent posts from the Elden Ring team?",
                    "Check updates for Cyberpunk 2077",
                ],
                cache_examples=False,
                submit_btn="Send",
            )

        # Right — followed games panel
        with gr.Column(scale=1, min_width=180):
            gr.HTML('<div id="followed-label">Following</div>')
            followed_display.render()


# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch(theme=THEME, css=CSS)
