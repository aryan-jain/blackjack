import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd
from textual.containers import Container, ScrollableContainer
from textual.widgets import Static


class Suit(Enum):
    HEARTS = 1
    DIAMONDS = 2
    CLUBS = 3
    SPADES = 4


class Rank(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13


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


@dataclass
class Player:
    name: str
    balance: int = 0

    def get_balance(self):
        return f"${self.balance / 100:.2f}"


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


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)
    dealer: bool = False

    def __str__(self):
        if self.dealer:
            return f"{self.cards[0]} [ ? ]"
        else:
            return " ".join([str(card) for card in self.cards])

    def add_card(self, card: Card):
        self.cards.append(card)

    def get_hand(self) -> str:
        if self.dealer:
            card = self.cards[0]
            match card.rank:
                case Rank.ACE:
                    return "A"
                case Rank.JACK | Rank.QUEEN | Rank.KING | Rank.TEN:
                    return "10"
                case _:
                    return str(card.rank.value)
        else:
            if len(self.cards) == 2:
                card1 = min(self.cards[0].rank.value, 10)
                card2 = min(self.cards[1].rank.value, 10)

                if card1 == card2:
                    match card1:
                        case 1:
                            return "A,A"
                        case _:
                            return f"{card1},{card2}"
                else:
                    match [card1, card2]:
                        case [1, _]:
                            return f"A,{card2}"
                        case [_, 1]:
                            return f"A,{card1}"
                        case _:
                            return f"{card1 + card2}"
            else:
                _, total11 = self.get_total()
                return str(total11)

    def get_total(self) -> tuple[int, int]:
        total1 = 0
        total11 = 0

        for card in self.cards:
            if card.rank.value >= 2 and card.rank.value <= 10:
                total1 += card.rank.value
                total11 += card.rank.value
            elif card.rank.value >= 11 and card.rank.value <= 13:
                total1 += 10
                total11 += 10
            elif card.rank.value == 1:
                if total1 + 11 > 21:
                    total1 += 1
                    total11 += 1
                else:
                    total1 += 1
                    total11 += 11

        return total1, total11


class StrategyMove(Enum):
    HIT = "H"
    STAND = "S"
    DOUBLE = "D"
    SPLIT = "Y"
    DONT_SPLIT = "N"
    SURRENDER = "SUR"
    DOUBLE_ALLOWED = "Ds"


class Strategy:
    def __init__(self) -> None:
        self.hard_totals = pd.read_csv("src/data/hard_totals.csv").set_index("Hand")
        self.soft_totals = pd.read_csv("src/data/soft_totals.csv").set_index("Hand")
        self.splits = pd.read_csv("src/data/splits.csv").set_index("Hand")

    def get_strategy(
        self, player_hand: Hand, dealer_hand: Hand
    ) -> Optional[StrategyMove]:
        dealer_card = dealer_hand.get_hand()
        player_cards = player_hand.get_hand()

        cards = player_cards.split(",")

        if len(cards) == 2:
            if cards[0] == cards[1]:
                split_strategy = self.splits.loc[player_cards, dealer_card]
                if split_strategy == StrategyMove.SPLIT.value:
                    return StrategyMove.SPLIT
            if cards[0] == "A":
                soft_strategy = self.soft_totals.loc[player_cards, dealer_card]
                return StrategyMove(soft_strategy)

        _, total11 = player_hand.get_total()

        match [total11, dealer_card]:
            case [16, "9" | "10" | "A"]:
                return StrategyMove.SURRENDER
            case [15, "10"]:
                return StrategyMove.SURRENDER

        if total11 >= 17:
            hard_strategy = self.hard_totals.loc[">= 17", dealer_card]
        elif total11 <= 8:
            hard_strategy = self.hard_totals.loc["<= 8", dealer_card]
        else:
            hard_strategy = self.hard_totals.loc[str(total11), dealer_card]

        return StrategyMove(hard_strategy)


class QuickAccess(Container):
    pass


class Body(ScrollableContainer):
    pass


class Title(Static):
    pass


class Section(Container):
    pass


class Column(Container):
    pass


class TextContent(Static):
    pass


class Window(Container):
    pass


class SubTitle(Static):
    pass


class SectionTitle(Static):
    pass


class Message(Static):
    pass


class AboveFold(Container):
    pass
