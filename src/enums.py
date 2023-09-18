from enum import Enum


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


class HandState(Enum):
    ACTIVE = 1
    BUST = 2
    STAND = 3
    BLACKJACK = 4
    SURRENDER = 5


class StrategyMove(Enum):
    HIT = "H"
    STAND = "S"
    DOUBLE = "D"
    SPLIT = "Y"
    DONT_SPLIT = "N"
    SURRENDER = "SUR"
    DOUBLE_ALLOWED = "Ds"
