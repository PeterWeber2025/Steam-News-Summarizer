---
title: Steam News Summarizer
emoji: 🏢
colorFrom: red
colorTo: purple
sdk: gradio
sdk_version: 6.14.0
app_file: app.py
pinned: false
short_description: A way to automatically get recent new on Steam games
---

huggingface link: https://huggingface.co/spaces/Peter-W2004/Steam-News-Summarizer

### Overview — What does this bot do and who is it for? (2–3 sentences)
This bot provides a way to quickly find the most recent news from the developers of games your interested in by calling the Steam API and using an LLM + Gradio.

### The Problem — What frustration or need motivated this? Why does it matter? (1 paragraph)
On Steam the only way to learn if a developer has posted news related to a game your interested in is to manually check each game of interest. Which is fine if you are looking at 2-3 games and tedious if you are looking at 10-12. I like learning when developers update games and add new features but don't make it a habit to check if they have because it's tedious, this application makes it easier to learn about the most recent news related to games I like.

### How It Works — A diagram or description of your bot's routing logic. Show which tools exist and how the bot decides which one to use.
<img width="800" height="289" alt="steam_news_bot_routing_v5(1)" src="https://github.com/user-attachments/assets/fadae143-d354-4fc9-8378-da484e5361e2" />

### Key Findings / What I Learned
Figuring out the routing logic of my bot, Gradio UI formatting.


### Sample Conversations 
WIP

### How to Run 
Either download the repo, and add file titled "key.env" which contains a variable titled GOOGLE_API_KEY, and it's corresponding value, or click the link to the huggingface website and make sure you have a secret titled GOOGLE_API_KEY, with you API key.

You can make a GOOGLE_API_KEY here: https://aistudio.google.com/api-keys

### Who Would Care
People who enjoy tracking news related to games they enjoy might appreciate this. It could be helpful with determining what games to play (based on what's been updated recently/added new content).
