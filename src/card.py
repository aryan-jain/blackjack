import random
from dataclasses import dataclass, field

from enums import Rank, Suit


@dataclass
class Card:
    suit: Suit
    rank: Rank

    def __str__(self):
        match self.suit:
            case Suit.HEARTS:
                suit = "♥️"
            case Suit.DIAMONDS:
                suit = "♦️"
            case Suit.CLUBS:
                suit = "♣️"
            case Suit.SPADES:
                suit = "♠️"

        match self.rank:
            case Rank.ACE:
                rank = "A"
            case Rank.JACK:
                rank = "J"
            case Rank.QUEEN:
                rank = "Q"
            case Rank.KING:
                rank = "K"
            case _:
                rank = str(self.rank.value)

        return f"[{rank}{suit}]"

    def unicode(self) -> str:
        ret = 127136
        match self.suit:
            case Suit.HEARTS:
                ret += 16
            case Suit.DIAMONDS:
                ret += 16 * 2
            case Suit.CLUBS:
                ret += 16 * 3

        ret += self.rank.value
        return "&#" + hex(ret)[1:] + ";"


@dataclass
class Shoot:
    decks: int
    count: int = 0
    cards: list[Card] = field(init=False, default_factory=list)
    reshuffle: int = field(init=False)

    def __post_init__(self):
        self.cards = [Card(suit, rank) for suit in Suit for rank in Rank] * self.decks
        random.shuffle(self.cards)
        self.reshuffle = int(len(self.cards) * 0.15)

    def cut(self, pos: int):
        self.cards = self.cards[pos:] + self.cards[:pos]

    def draw(self) -> Card:
        card = self.cards.pop()
        if card.rank.value >= 2 and card.rank.value <= 6:
            self.count += 1
        elif card.rank.value == 1 or card.rank.value >= 10:
            self.count -= 1

        return card
