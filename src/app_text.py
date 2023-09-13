WELCOME = """
Welcome to Blackjack!
A terminal app by Aryan Jain.
"""

RULES = """
Welcome to BlackJack! This is a simple game of BlackJack that you can play with your friends. 
The rules are simple, get as close to 21 as possible without going over. If you go over, you lose. 

## Card Values
Ace can be worth 1 or 11, whichever is better for you.
Jacks, Queens, and Kings are worth 10. 
All other cards are worth their face value.

## Payouts
If you get 21 on your first two cards, you get a BlackJack and win.
Blackjack pays 3 to 2, so if you bet $10, you get $15 back.
Every other win pays 1 to 1, so if you bet $10, you get $10 back.
If you go bust, you lose your bet.
There is a concept of insurance, which is a special case when dealer shows an Ace. We will go over that in the Dealer section below.

## Playing Your Turn
During your turn, you can choose to hit, stand, double, split or surrender.

### Hit
Draw another card. You may continue drawing cards until you go bust or choose to stand.

### Stand
End your turn.

### Double
You can only double on your first 2 cards. You double your bet and draw only 1 more card to end your turn.

### Split
If you have 2 cards of the same rank, you can split them into 2 hands. You must bet the same amount on the second hand. For now, this app only supports splitting once. In the future, I may add the ability to split multiple times.

### Surrender
You can only surrender on your first 2 cards. You lose half your bet and end your turn.

## Dealer
The dealer follows the following rules:
- Dealer stands on 17 or higher.
- If the dealer has 16 or lower, they must hit.
- If the dealer has an Ace, they must hit on soft 17.

## Insurance
If the dealer shows an Ace, you can choose to take insurance. Insurance costs half your bet. 
If the dealer has a BlackJack, you win 2 to 1 on your insurance bet. 
If the dealer does not have a BlackJack, you lose your insurance bet. 
Either way, the game continues as normal.
"""


STRATEGY_INTRO = """
The `Hand` column represents the player's hand. The other columns represent the dealer's face up card.
"""
