#!/usr/bin/env python3
"""
Blackjack - Command Line Edition
Run with: python blackjack.py
"""

import random
import os
import sys

# ── Card & Deck ───────────────────────────────────────────────

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']

class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def value(self):
        if self.rank in ['J','Q','K']:
            return 10
        if self.rank == 'A':
            return 11
        return int(self.rank)

    def __str__(self):
        return f"{self.suit}{self.rank}"

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in SUITS for r in RANKS]
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

# ── Hand Logic ────────────────────────────────────────────────

def hand_value(hand):
    total = sum(c.value() for c in hand)
    aces = sum(1 for c in hand if c.rank == 'A')
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

def show_hand(name, hand, hide_first=False):
    if hide_first:
        cards = ["??"] + [str(c) for c in hand[1:]]
        print(f"  {name}: {' '.join(cards)}")
    else:
        print(f"  {name}: {' '.join(str(c) for c in hand)}  (value: {hand_value(hand)})")

# ── Game Flow ─────────────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_choice(prompt, choices):
    while True:
        choice = input(prompt).strip().lower()
        if choice in choices:
            return choice
        print("  Invalid choice. Try again.")

def play_round(balance):
    # Bet
    print(f"\n  💰 Your balance: ${balance}")
    while True:
        try:
            bet = int(input("  Place your bet: $"))
            if 1 <= bet <= balance:
                break
            print("  Bet must be between $1 and your balance.")
        except ValueError:
            print("  Enter a valid number.")

    deck = Deck()
    player = [deck.draw(), deck.draw()]
    dealer = [deck.draw(), deck.draw()]

    # ── Player Turn ──
    while True:
        clear()
        print("\n  🎰 BLACKJACK 🎰\n")
        show_hand("Dealer", dealer, hide_first=True)
        show_hand("You   ", player)

        if hand_value(player) == 21:
            print("\n  🎉 BLACKJACK!")
            break
        if hand_value(player) > 21:
            print("\n  💥 Bust! You went over 21.")
            return balance - bet

        action = get_choice("\n  [H]it or [S]tand? ", ['h', 's', 'hit', 'stand'])
        if action in ('h', 'hit'):
            player.append(deck.draw())
        else:
            break

    player_total = hand_value(player)
    if player_total > 21:
        return balance - bet

    # ── Dealer Turn ──
    clear()
    print("\n  🎰 BLACKJACK 🎰\n")
    print("  Dealer reveals their hand...\n")

    while hand_value(dealer) < 17:
        dealer.append(deck.draw())

    show_hand("Dealer", dealer)
    show_hand("You   ", player)

    dealer_total = hand_value(dealer)

    print()
    if dealer_total > 21:
        print("  Dealer busts! You win! 🎉")
        return balance + bet
    elif dealer_total > player_total:
        print(f"  Dealer wins with {dealer_total}. 😞")
        return balance - bet
    elif dealer_total < player_total:
        print(f"  You win with {player_total}! 🎉")
        return balance + bet
    else:
        print("  It's a push (tie). Your bet is returned. 🤝")
        return balance

# ── Main ──────────────────────────────────────────────────────

def main():
    balance = 100
    clear()
    print("""
   ██████╗ ██╗      █████╗  ██████╗██╗  ██╗     ██╗ █████╗  ██████╗██╗  ██╗
   ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝     ██║██╔══██╗██╔════╝██║ ██╔╝
   ██████╔╝██║     ███████║██║     █████╔╝      ██║███████║██║     █████╔╝ 
   ██╔══██╗██║     ██╔══██║██║     ██╔═██╗ ██   ██║██╔══██║██║     ██╔═██╗ 
   ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗╚█████╔╝██║  ██║╚██████╗██║  ██╗
   ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
    """)
    print("  Welcome to CLI Blackjack! You start with $100.")
    print("  Beat the dealer by getting closer to 21 without going over.\n")
    input("  Press Enter to start...")

    while balance > 0:
        balance = play_round(balance)
        if balance <= 0:
            clear()
            print("\n  💀 You're out of money! Game over.\n")
            break
        again = get_choice("\n  Play again? [Y/n] ", ['y', 'n', 'yes', 'no', ''])
        if again in ('n', 'no'):
            break

    clear()
    print(f"\n  👋 Thanks for playing! You leave with ${balance}.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Game interrupted. See you next time!")
        sys.exit(0)
