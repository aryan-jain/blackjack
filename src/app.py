import asyncio
from pathlib import Path
from typing import Optional

from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.reactive import reactive, var
from textual.validation import Function, Number
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Pretty,
    Rule,
    Static,
)

from card import Shoot
from classes import (
    AboveFold,
    Body,
    Column,
    QuickAccess,
    Section,
    SectionTitle,
    SubTitle,
    TextContent,
)
from enums import HandState
from hand import Hand, HandDisplay
from src.app_text import RULES, STRATEGY_INTRO, WELCOME
from strategy import Strategy

STRATEGY = Strategy()


class LocationLink(Static):
    def __init__(self, label: str, reveal: str) -> None:
        super().__init__(label)
        self.reveal = reveal

    def on_click(self) -> None:
        self.app.query_one(self.reveal).scroll_visible(top=True, duration=0.5)


class Welcome(Container):
    def compose(self) -> ComposeResult:
        yield Static(Markdown(WELCOME))
        yield Button("Start", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.query_one(".location-rules").scroll_visible(duration=0.5, top=True)


class BlackjackApp(App):
    TITLE = "Blackjack"
    SUB_TITLE = "© Aryan Jain"
    BINDINGS = [
        ("ctrl+t", "toggle_dark", "Toggle dark mode"),
    ]
    CSS_PATH = Path(__file__).parent / "css/style.tcss"

    balance = var(0)
    player_balance = reactive("")
    hand_idx = var(0)

    dealer_str = reactive("")
    dealer_total = reactive("")

    count = reactive(0)
    cards_remaining = reactive(0)

    recommended_strategy = reactive("")

    def compose(self) -> ComposeResult:
        yield Container(
            Header(),
            Body(
                QuickAccess(
                    LocationLink("Home", ".location-top"),
                    LocationLink("Rules", ".location-rules"),
                    LocationLink("Strategy", ".location-strategy"),
                    LocationLink("Play", ".location-play"),
                ),
                AboveFold(Welcome(), classes="location-top"),
                Column(
                    Section(SectionTitle("Rules"), TextContent(Markdown(RULES))),
                    classes="location-rules",
                ),
                Column(
                    Section(
                        SectionTitle("Strategy"),
                        DataTable(id="strategy-legend"),
                        TextContent(Markdown(STRATEGY_INTRO)),
                        TextContent(Text("Hard Totals", style="bold")),
                        DataTable(id="hard-totals"),
                        TextContent(Text("Soft Totals", style="bold")),
                        DataTable(id="soft-totals"),
                        TextContent(Text("Splits", style="bold")),
                        DataTable(id="splits_table"),
                        TextContent(Text("Surrender", style="bold")),
                        DataTable(id="surrender_table"),  # type: ignore
                        TextContent(
                            Markdown(
                                "#### Insurance or even money is never recommended."
                            )
                        ),
                    ),
                    classes="location-strategy",
                ),
                Column(
                    Section(
                        SectionTitle("Play"),
                        Label("Buy In: "),
                        Input(
                            placeholder="Buy In",
                            id="buy_in",
                            validators=[Number(minimum=10, maximum=10000)],
                        ),
                        Label("Number of Decks: "),
                        Input(
                            placeholder="Number of Decks",
                            id="num_decks",
                            validators=[Number(minimum=1, maximum=8)],
                        ),
                        Pretty([], id="num_decks_errors"),
                        Button("Start Game", id="start_game", variant="warning"),
                        Rule(line_style="thick"),
                    ),
                    classes="location-play",
                ),
                Column(
                    Section(
                        SectionTitle("Game"),
                        TextContent(
                            Text(f"Cards remaining: {self.cards_remaining}"),
                            id="cards_remaining",
                        ),
                        TextContent(Text(f"Count: {self.count}"), id="count_display"),
                        SubTitle("Dealer"),
                        SubTitle(self.dealer_str, id="dealer_str_display"),
                        SubTitle(
                            f"Total: {self.dealer_total}", id="dealer_total_display"
                        ),
                        Rule(),
                        ScrollableContainer(id="player_hands", classes="player_hands"),
                        Horizontal(
                            Button("Hit", id="hit", variant="primary", disabled=True),
                            Button(
                                "Stand", id="stand", variant="warning", disabled=True
                            ),
                            Button(
                                "Double", id="double", variant="success", disabled=True
                            ),
                            Button(
                                "Split", id="split", variant="success", disabled=True
                            ),
                            Button(
                                "Surrender",
                                id="surrender",
                                variant="error",
                                disabled=True,
                            ),
                            classes="buttons",
                        ),
                        TextContent(
                            Text(
                                f"Strategy Recommendation: {self.recommended_strategy}"
                            ),
                            id="strategy_recommendation",
                        ),
                        TextContent(f"Balance: {self.player_balance}", id="balance"),
                        Label("Bet: "),
                        Input(
                            placeholder="Bet",
                            id="bet",
                            validators=[
                                Function(
                                    self.is_valid_bet,
                                    "Bet must be a multiple of 10 and less than your balance",
                                )
                            ],
                        ),
                        Pretty([], id="bet_errors"),
                        Button("Deal", id="deal", variant="success"),
                        id="game",
                    ),
                    classes="location-game",
                ),
            ),
        )
        yield Footer()

    def is_valid_bet(self, bet: str) -> bool:
        try:
            return (
                int(bet) >= 10
                and int(bet) <= int(self.balance / 100)
                and (int(bet) % 10 == 0)
            )
        except ValueError:
            return False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "start_game":
                event.button.disabled = True
                buy_in = self.query_one("#buy_in", expect_type=Input).value
                self.balance = int(buy_in) * 100
                self.player_balance = f"${self.balance / 100:.2f}"

                self.num_decks = self.query_one("#num_decks", expect_type=Input)
                self.shoot = Shoot(decks=int(self.num_decks.value))
                self.cards_remaining = len(self.shoot.cards) - self.shoot.reshuffle

                self.app.query_one(".location-game").scroll_visible(
                    duration=0.5, top=True
                )

            case "deal":
                while hands := self.query(HandDisplay):
                    hands.last().remove()
                self.hand_idx = 0
                hand = Hand()
                self.active_hand = HandDisplay(hand=hand)
                self.active_hand.add_class("active")
                await self.query_one("#player_hands").mount(self.active_hand)

                hand.bet = int(self.query_one("#bet", expect_type=Input).value)
                self.balance -= hand.bet * 100
                self.player_balance = f"${self.balance / 100:.2f}"

                self.dealer_hand = Hand(dealer=True)

                for _ in range(2):
                    await self.draw_card()
                    await self.draw_card(dealer=True)

                self.dealer_str = str(self.dealer_hand)

                _, total11 = hand.get_total()
                if total11 == 21:
                    hand.state = HandState.BLACKJACK
                else:
                    self.query_one("#hit").disabled = False
                    self.query_one("#double").disabled = False

                card1, card2 = hand.cards
                if min(card1.rank.value, 10) == min(card2.rank.value, 10):
                    self.query_one("#split").disabled = False

                self.query_one("#stand").disabled = False
                self.query_one("#surrender").disabled = False

                self.recommended_strategy = STRATEGY.get_strategy(
                    hand, self.dealer_hand
                ).name

            case "hit":
                await self.hit()
                if self.active_hand.hand.state == HandState.BUST:
                    await self.stand()

            case "stand":
                await self.stand()

            case "double":
                self.active_hand.hand.bet *= 2
                self.balance -= self.active_hand.hand.bet * 100
                self.player_balance = f"${self.balance / 100:.2f}"
                await self.hit()
                await self.stand()

            case "surrender":
                await self.surrender()

            case "split":
                await self.split()

    async def hit(self):
        hand = self.active_hand.hand

        await self.draw_card()
        self.query_one("#double").disabled = True
        self.query_one("#split").disabled = True

        total1, total11 = hand.get_total()
        if total1 >= 21 or total11 == 21:
            self.query_one("#hit").disabled = True
            self.query_one("#surrender").disabled = True

        self.recommended_strategy = STRATEGY.get_strategy(hand, self.dealer_hand).name

        await self.active_hand.update()

    async def stand(self):
        self.active_hand.remove_class("active")
        self.active_hand.add_class("inactive")

        if self.active_hand.hand.state == HandState.ACTIVE:
            self.active_hand.hand.state = HandState.STAND

        hands = self.query(HandDisplay)
        if self.hand_idx < len(hands) - 1:
            self.hand_idx += 1
            self.active_hand = hands[self.hand_idx]
            self.active_hand.remove_class("inactive")
            self.active_hand.add_class("active")
            self.active_hand.scroll_visible()
            if len(self.active_hand.hand.cards) < 2:
                await self.draw_card()
            await self.active_hand.update()

            _, total11 = self.active_hand.hand.get_total()
            if total11 == 21:
                self.active_hand.hand.state = HandState.BLACKJACK
            else:
                self.query_one("#hit").disabled = False
                self.query_one("#double").disabled = False
                self.query_one("#split").disabled = False

            self.query_one("#stand").disabled = False
            self.query_one("#surrender").disabled = False

        else:
            await self.end_round()

    async def surrender(self):
        self.active_hand.hand.state = HandState.SURRENDER
        self.balance += self.active_hand.hand.bet * 50
        self.player_balance = f"${self.balance / 100:.2f}"
        await self.active_hand.update()
        await self.stand()

    async def split(self):
        hand = self.active_hand.hand
        split_card = hand.cards.pop()

        self.balance = self.balance - hand.bet * 100
        self.player_balance = f"${self.balance / 100:.2f}"

        await self.draw_card()

        new_hand = HandDisplay(
            hand=Hand(bet=self.active_hand.hand.bet), classes="inactive"
        )
        new_hand.hand.add_card(split_card)
        await self.query_one("#player_hands").mount(new_hand)

        await new_hand.update()
        self.refresh()
        self.refresh_css(animate=True)

    async def end_round(self) -> None:
        self.query_one("#hit").disabled = True
        self.query_one("#stand").disabled = True
        self.query_one("#double").disabled = True
        self.query_one("#split").disabled = True
        self.query_one("#surrender").disabled = True
        self.query_one("#deal").disabled = False

        # Run Dealer Hand
        self.dealer_hand.dealer = False
        total1, total11 = self.dealer_hand.get_total()
        while total1 < 17 and total11 < 18:
            await self.draw_card(dealer=True)
            total1, total11 = self.dealer_hand.get_total()

        self.dealer_str = str(self.dealer_hand)
        self.dealer_total = f"Total: {total11}"

        hands = self.query(HandDisplay)

        for hand in hands:
            match hand.hand.state:
                case HandState.BLACKJACK:
                    hand.result = f"Blackjack! You win ${hand.hand.bet*1.5:.2f}!"
                    self.balance += hand.hand.bet * 250
                case HandState.BUST:
                    hand.result = f"BUST! You lose ${hand.hand.bet:.2f}!"
                case HandState.SURRENDER:
                    hand.result = f"Surrendered! You get back ${hand.hand.bet*0.5:.2f}!"
                    self.balance += hand.hand.bet * 150
                case HandState.STAND:
                    _, player_total = hand.hand.get_total()
                    if total1 > 21:
                        hand.result = f"Dealer BUSTS! You win ${hand.hand.bet:.2f}!"
                        self.balance += hand.hand.bet * 200
                    elif total11 > player_total:
                        hand.result = f"Dealer wins! You lose ${hand.hand.bet:.2f}!"
                    elif total11 == player_total:
                        hand.result = f"Push! You get back ${hand.hand.bet:.2f}!"
                        self.balance += hand.hand.bet * 100
                    else:
                        hand.result = f"You win ${hand.hand.bet:.2f}!"
                        self.balance += hand.hand.bet * 200
            await hand.update()

        self.player_balance = f"${self.balance / 100:.2f}"

    async def draw_card(self, dealer: bool = False) -> None:
        if dealer:
            hand = self.dealer_hand
            hand.add_card(self.shoot.draw())
            total1, total11 = hand.get_total()
            if total11 == 21 and len(hand.cards) == 2:
                hand.state = HandState.BLACKJACK
                if dealer:
                    self.dealer_total = "Blackjack :("
            elif total1 > 21:
                hand.state = HandState.BUST
                if dealer:
                    self.dealer_total = "BUST!"
            else:
                self.dealer_total = f"Total: {total11}"
        else:
            hand = self.active_hand.hand
            hand.add_card(self.shoot.draw())
            await self.active_hand.update()

        self.cards_remaining = len(self.shoot.cards) - self.shoot.reshuffle
        self.count = self.shoot.count

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        match event.input.id:
            case "num_decks":
                error = "#num_decks_errors"
            case "bet":
                error = "#bet_errors"
            case _:
                return

        if event.validation_result and not event.validation_result.is_valid:
            self.query_one(error, expect_type=Pretty).update(
                event.validation_result.failure_descriptions
            )
        else:
            self.query_one(error, expect_type=Pretty).update([])

    def on_mount(self) -> None:
        lookup = {
            "hard-totals": STRATEGY.hard_totals,
            "soft-totals": STRATEGY.soft_totals,
            "splits_table": STRATEGY.splits,
        }

        for strategy in [
            "hard-totals",
            "soft-totals",
            "splits_table",
            "surrender_table",
        ]:
            match strategy:
                case "surrender_table":
                    table: DataTable = self.app.query_one(
                        "#surrender_table", expect_type=DataTable
                    )
                    columns = ["Hand", "9", "10", "A"]
                    rows = [
                        (
                            16,
                            Text("SUR", style="bold red"),
                            Text("SUR", style="bold red"),
                            Text("SUR", style="bold red"),
                        ),
                        (15, "", Text("SUR", style="bold red"), ""),
                    ]
                    table.add_columns(*columns)
                    table.add_rows(rows)

                case _:
                    table: DataTable = self.app.query_one(
                        f"#{strategy}", expect_type=DataTable
                    )
                    self.data = lookup[strategy].reset_index()
                    table.add_columns(*[str(x) for x in self.data.columns])
                    for row in self.data.itertuples(index=False):
                        styled_row = []
                        for cell in row:
                            match str(cell):
                                case "H":
                                    styled_row.append(Text(str(cell), style="bold"))
                                case "S":
                                    styled_row.append(
                                        Text(str(cell), style="bold yellow")
                                    )
                                case "D":
                                    styled_row.append(
                                        Text(str(cell), style="bold green")
                                    )
                                case "Ds":
                                    styled_row.append(
                                        Text(str(cell), style="bold green")
                                    )
                                case "Y":
                                    styled_row.append(
                                        Text(str(cell), style="bold green")
                                    )
                                case "N":
                                    styled_row.append(Text(str(cell), style="bold red"))
                                case "SUR":
                                    styled_row.append(Text(str(cell), style="bold red"))
                                case _:
                                    styled_row.append(Text(str(cell)))
                        table.add_row(*styled_row)

        table: DataTable = self.app.query_one("#strategy-legend", expect_type=DataTable)
        table.add_columns("Strategy", "Description")
        rows = [
            (Text("H", style="bold"), "Hit"),
            (Text("S", style="bold yellow"), "Stand"),
            (Text("D", style="bold green"), "Double"),
            (Text("Ds", style="bold green"), "Double if allowed, otherwise Stand"),
            (Text("Y", style="bold green"), "Split"),
            (Text("N", style="bold red"), "Don't Split"),
            (Text("SUR", style="bold red"), "Surrender"),
        ]
        table.add_rows(rows)

    def action_toggle_dark(self):
        self.dark = not self.dark

    async def watch_recommended_strategy(self, value: str) -> None:
        await self.mount()
        self.query_one("#strategy_recommendation", expect_type=TextContent).update(
            Text(f"Strategy Recommendation: {value}")
        )

    async def watch_count(self, value: int) -> None:
        await self.mount()
        self.query_one("#count_display", expect_type=TextContent).update(
            Text(f"Count: {value}")
        )

    async def watch_cards_remaining(self, value: int) -> None:
        await self.mount()
        self.query_one("#cards_remaining", expect_type=TextContent).update(
            Text(f"Cards remaining: {value}")
        )

    async def watch_dealer_str(self, value: str) -> None:
        await self.mount()
        self.query_one("#dealer_str_display", expect_type=SubTitle).update(value)

    async def watch_dealer_total(self, value: str) -> None:
        await self.mount()
        self.query_one("#dealer_total_display", expect_type=SubTitle).update(value)

    async def watch_player_balance(self, value: str) -> None:
        await self.mount()
        self.query_one("#balance", expect_type=TextContent).update(
            Text(f"Balance: {value}")
        )


if __name__ == "__main__":
    app = BlackjackApp()
    app.run()
