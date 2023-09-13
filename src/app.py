import time
from pathlib import Path
from typing import Optional
from bkp.pages.1_Play import play

from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.validation import Function, Number
from textual.widgets import (
    Button,
    DataTable,
    Digits,
    Footer,
    Header,
    Input,
    Label,
    Pretty,
    Rule,
    Static,
)

from classes import (
    AboveFold,
    Body,
    Column,
    Hand,
    Player,
    QuickAccess,
    Section,
    SectionTitle,
    Shoot,
    Strategy,
    SubTitle,
    TextContent,
)
from src.app_text import RULES, STRATEGY_INTRO, WELCOME

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


class CreatePlayer(Container):
    player: Optional[Player] = None

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Name: "),
            Input(placeholder="Name", id="name"),
            Label("Buy In: "),
            Input(placeholder="Buy In", id="buy_in"),
            Pretty([]),
            Button(
                "Save Player",
                id="create_player",
                variant="success",
                disabled=self.player is not None,
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_player":
            name = self.query_one("#name", expect_type=Input).value
            buy_in = self.query_one("#buy_in", expect_type=Input).value
            self.player = Player(name=name, balance=int(buy_in) * 100)

            # self.app.query_one(".location-play").scroll_visible(duration=0.5, top=True)

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.input.id == "buy_in":
            if event.validation_result and not event.validation_result.is_valid:
                self.query_one(Pretty).update(
                    event.validation_result.failure_descriptions
                )
            else:
                self.query_one(Pretty).update([])


class BlackjackApp(App):
    TITLE = "Blackjack"
    SUB_TITLE = "© Aryan Jain"
    BINDINGS = [
        ("ctrl+t", "toggle_dark", "Toggle dark mode"),
    ]
    CSS_PATH = Path(__file__).parent / "css/style.tcss"

    player_balance = reactive("")

    dealer_unicode = reactive("")
    dealer_str = reactive("")
    player_unicode = reactive("")
    player_str = reactive("")

    dealer_total = reactive("")
    player_total = reactive("")

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
                        # Horizontal(
                        #     Button("Add Player", id="add_player", variant="success"),
                        #     Button(
                        #         "Remove Player", id="remove_player", variant="error"
                        #     ),
                        # ),
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
                        # TextContent(
                        #     Markdown("# " + self.dealer_unicode),
                        #     classes="hand",
                        #     id="dealer_hand",
                        # ),
                        SubTitle(self.dealer_str, id="dealer_str_display"),
                        SubTitle(
                            f"Total: {self.dealer_total}", id="dealer_total_display"
                        ),
                        Rule(),
                        TextContent(id="result"),
                        SubTitle("Player"),
                        # TextContent(
                        #     Markdown("# " + self.player_unicode),
                        #     classes="hand",
                        #     id="player_hand",
                        # ),
                        SubTitle(self.player_str, id="player_str_display"),
                        SubTitle(
                            f"Total: {self.player_total}", id="player_total_display"
                        ),
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

    # async def watch_dealer_unicode(self, value: str) -> None:
    #     await self.mount()
    #     self.query_one("#dealer_hand", expect_type=TextContent).update(
    #         Markdown(f"# {value}")
    #     )

    # async def watch_player_unicode(self, value: str) -> None:
    #     await self.mount()
    #     self.query_one("#player_hand", expect_type=TextContent).update(
    #         Markdown(f"# {value}")
    #     )

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

    async def watch_player_str(self, value: str) -> None:
        await self.mount()
        self.query_one("#player_str_display", expect_type=SubTitle).update(value)

    async def watch_player_total(self, value: str) -> None:
        await self.mount()
        self.query_one("#player_total_display", expect_type=SubTitle).update(value)

    async def watch_player_balance(self, value: int) -> None:
        await self.mount()
        self.query_one("#balance", expect_type=TextContent).update(
            Text(f"Balance: {value}")
        )

    def is_valid_bet(self, bet: str) -> bool:
        try:
            return (
                int(bet) >= 10
                and int(bet) <= int(self.player.balance / 100)
                and (int(bet) % 10 == 0)
            )
        except ValueError:
            return False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # if event.button.id == "add_player":
        #     self.query_one("#players").mount(CreatePlayer())
        # elif event.button.id == "remove_player":
        #     players = self.query("CreatePlayer")
        #     if players:
        #         players.last().remove()
        match event.button.id:
            case "start_game":
                event.button.disabled = True
                buy_in = self.query_one("#buy_in", expect_type=Input).value
                self.player = Player("player", int(buy_in) * 100)

                self.num_decks = self.query_one("#num_decks", expect_type=Input)
                self.shoot = Shoot(decks=int(self.num_decks.value))
                self.cards_remaining = len(self.shoot.cards) - self.shoot.reshuffle

                self.app.query_one(".location-game").scroll_visible(
                    duration=0.5, top=True
                )

            case "deal":
                if not self.player:
                    return
                else:
                    self.player.balance -= (
                        int(self.query_one("#bet", expect_type=Input).value) * 100
                    )
                    self.player_balance = self.player.balance / 100

                    self.dealer_hand = Hand(dealer=True)

                    for _ in range(2):
                        self.draw_card(self.player.hand, False)
                        self.draw_card(self.dealer_hand, True)

                    self.query_one("#hit").disabled = False
                    self.query_one("#stand").disabled = False
                    self.query_one("#double").disabled = False
                    self.query_one("#split").disabled = False
                    self.query_one("#surrender").disabled = False

                    self.recommended_strategy = STRATEGY.get_strategy(
                        self.player.hand, self.dealer_hand
                    ).name

            case "hit":
                self.hit()

            case "stand":
                self.stand()

    def hit(self):
        self.draw_card(self.player.hand, False)
        self.query_one("#double").disabled = True
        self.query_one("#split").disabled = True

        self.recommended_strategy = STRATEGY.get_strategy(
            self.player.hand, self.dealer_hand
        )

        total1, total11 = self.player.hand.get_total()
        if total1 >= 21 or total11 == 21:
            self.query_one("#hit").disabled = True
            self.query_one("#double").disabled = True
            self.query_one("#split").disabled = True
            self.query_one("#surrender").disabled = True

    def stand(self):
        self.dealer_hand.dealer = False
        _, player_total = self.player.hand.get_total()
        total1, total11 = self.dealer_hand.get_total()

        if player_total == 21 and len(self.player.hand.cards) == 2:
            pass


        while total1 < 17 and total11 < 18:
            self.draw_card(self.dealer_hand, True)
            total1, total11 = self.dealer_hand.get_total()
        


    def play_dealer(self):
        pass

    def draw_card(self, hand: Hand, dealer: bool) -> None:
        hand.add_card(self.shoot.draw())
        total1, total11 = hand.get_total()
        if total11 == 21 and len(hand.cards) == 2:
            blackjack = True
        else:
            blackjack = False

        if dealer:
            self.dealer_unicode = hand.unicode()
            self.dealer_str = str(hand)
            if blackjack:
                self.dealer_total = "Blackjack :("
            elif total1 > 21:
                self.dealer_total = "BUST!"
            else:
                self.dealer_total = f"Total: {total11}"
        else:
            self.player_unicode = hand.unicode()
            self.player_str = str(hand)
            if blackjack:
                self.player_total = "Blackjack! :)"
            elif total1 > 21:
                self.player_total = "BUST!"
            else:
                self.player_total = (
                    f"Total: {total1}/{total11}"
                    if total1 != total11
                    else f"Total: {total1}"
                )
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


if __name__ == "__main__":
    app = BlackjackApp()
    app.run()
