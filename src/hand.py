from dataclasses import dataclass, field

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget

from card import Card
from classes import TextContent
from enums import HandState, Rank


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)
    dealer: bool = False
    bet: int = 0
    state: HandState = HandState.ACTIVE

    def __str__(self):
        if self.dealer:
            return f"{self.cards[0]} [ ? ]"
        else:
            return " ".join([str(card) for card in self.cards])

    def unicode(self) -> str:
        if self.dealer:
            return f"{self.cards[0].unicode()} &#x1F0A0;"
        else:
            return " ".join([card.unicode() for card in self.cards])

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
        if self.dealer:
            match self.cards[0].rank:
                case Rank.ACE:
                    return 11, 11
                case Rank.JACK | Rank.QUEEN | Rank.KING | Rank.TEN:
                    return 10, 10
                case _:
                    return self.cards[0].rank.value, self.cards[0].rank.value

        total1 = 0
        total11 = 0

        for card in self.cards:  # Handle regular cards
            if card.rank.value >= 2 and card.rank.value <= 10:
                total1 += card.rank.value
                total11 += card.rank.value
            elif card.rank.value >= 11 and card.rank.value <= 13:
                total1 += 10
                total11 += 10
            elif card.rank.value == 1:
                continue

        for card in self.cards:  # Handle Aces
            if card.rank.value == 1:
                if total11 + 11 > 21:
                    total1 += 1
                    total11 += 1
                else:
                    total1 += 1
                    total11 += 11

        return total1, total11

    def get_bet(self) -> str:
        return f"${self.bet:.2f}"


class HandDisplay(Widget):
    cards = reactive("")
    total = reactive("")
    bet = reactive("")
    result = reactive("")

    def __init__(self, hand: Hand, **kwargs) -> None:
        super().__init__(**kwargs)
        self.hand = hand

    def compose(self) -> ComposeResult:
        yield TextContent(self.cards, id="hand_cards")
        yield TextContent(self.total, id="hand_total")
        yield TextContent(self.bet, id="hand_bet")
        yield TextContent(self.result, id="hand_result")

    def on_mount(self) -> None:
        self.cards = str(self.hand)
        total1, total11 = self.hand.get_total()
        if total11 == 21 and len(self.hand.cards) == 2:
            self.total = "Blackjack! :)"
        elif total1 > 21:
            self.total = "BUST!"
        elif total1 != total11:
            self.total = f"Total: {total1}/{total11}"
        else:
            self.total = f"Total: {total11}"

    async def update(self) -> None:
        await self.mount()
        self.log(self.tree)
        total1, total11 = self.hand.get_total()
        if total11 == 21 and len(self.hand.cards) == 2:
            self.total = "Blackjack! :)"
            self.hand.state = HandState.BLACKJACK
        elif total1 > 21:
            self.total = "BUST!"
            self.hand.state = HandState.BUST
        elif total1 != total11:
            self.total = f"Total: {total1}/{total11}"
        else:
            self.total = f"Total: {total11}"

        self.bet = self.hand.get_bet()

        self.query_one("#hand_cards", expect_type=TextContent).update(str(self.hand))
        self.query_one("#hand_total", expect_type=TextContent).update(self.total)
        self.query_one("#hand_bet", expect_type=TextContent).update(self.bet)
        self.query_one("#hand_result", expect_type=TextContent).update(self.result)
