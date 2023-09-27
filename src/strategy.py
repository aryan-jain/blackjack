from dataclasses import dataclass

import pandas as pd

from enums import StrategyMove
from hand import Hand


class Strategy:
    def __init__(self) -> None:
        self.hard_totals = pd.read_csv("src/data/hard_totals.csv").set_index("Hand")
        self.soft_totals = pd.read_csv("src/data/soft_totals.csv").set_index("Hand")
        self.splits = pd.read_csv("src/data/splits.csv").set_index("Hand")

    def get_strategy(self, player_hand: Hand, dealer_hand: Hand) -> StrategyMove:
        dealer_card = dealer_hand.get_hand()
        player_cards = player_hand.get_hand()

        if player_cards == "A,10":
            return StrategyMove.STAND

        cards = player_cards.split(",")

        if dealer_card not in self.splits.columns:
            return StrategyMove.STAND

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
