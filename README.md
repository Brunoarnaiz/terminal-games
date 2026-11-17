# Terminal Games

A small collection of games that run straight in your terminal — pure Python, no dependencies. A little gift for dead time.

## Games

| Game | Description | Run |
|---|---|---|
| **Marcianitos** | Space Invaders–style shooter built with `curses`: animated title screen, waves of enemies and a saved high score. | `python3 marcianitos.py` |
| **Blackjack** | Classic blackjack against the dealer, with a full deck and ace handling. | `python3 blackjack.py` |

### Marcianitos controls

`←` `→` move · `Space` shoot · `P` pause · `Q` quit

## Requirements

Python 3.8+. Marcianitos uses `curses`, which ships with Python on Linux and macOS (on Windows: `pip install windows-curses`).

```bash
git clone https://github.com/Brunoarnaiz/terminal-games.git
cd terminal-games
python3 marcianitos.py
```
