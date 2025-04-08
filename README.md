
# MafiosoNnad Bot v1.0.0
Created by @berlinnad

A feature-rich Telegram Mafia game bot with AI players, room management, and various game modes.

## Features
- 🎮 Multiple game modes (Normal, Random)
- 🤖 AI bot players with unique behaviors
- 👥 Room management system
- 🎭 Role system (Mafia, Detective, Doctor, etc)
- 📊 Player statistics tracking
- 🛍️ Shop system with items
- ⏰ Game timer management
- 👆 The Bot mostly uses buttons
## Known Issues/Bugs
- Room creation occasionally throws 'is_admin' keyword error
- Timer flood control in active games
- Button response delays in large groups

## Setup Instructions
1. Install required packages: `pip install -r requirements.txt`
2. Edit `config.py` and add your Telegram bot token and your ai api
3. Run `python main.py` to start the bot

## Commands
- /start - Start bot and show main menu
- /extend - Extend room timer
- /shop - Open shop menu

## Security
- Configuration is separate from main code
- Token management via config.py

## Credits
Created and maintained by @berlinnad
Copyright (c) 2024 Berlinnad. All rights reserved.
