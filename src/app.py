import time
from pathlib import Path
from typing import Optional

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


class GamePlayer(Container):
    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player
        self.hand = Hand()

    def compose(self) -> ComposeResult:
        in_progress = self.app.query_one("Game", expect_type=Game).in_progress

        total1, total11 = self.hand.get_total()

        hit = len(self.hand.cards) >= 2 and in_progress and total1 < 21
        double = len(self.hand.cards) == 2 and in_progress

        cards = self.hand.get_hand().split(",")
        split = len(cards) == 2 and cards[0] == cards[1] and in_progress

        total_str = f"{total1}/{total11}" if total1 != total11 else str(total1)

        yield Vertical(
            Label(self.player.name),
            Horizontal(
                Label("Balance: "), Digits(self.player.get_balance(), id="balance")
            ),
            Horizontal(
                Label("Bet: "),
                Input(
                    "Bet",
                    name="bet",
                    validators=[
                        Function(
                            self.is_valid_bet,
                            "Bet must be a multiple of 10 and less than your balance",
                        ),
                    ],
                    disabled=in_progress,
                ),
                Button("Bet", id="bet", variant="success", disabled=in_progress),
            ),
            Label("Hand: "),
            CardDisplay(id="player_hand"),
            TextContent(Text(total_str), classes="total", id="total"),
            Vertical(
                Horizontal(
                    Button("Hit", id="hit", variant="primary", disabled=not hit),
                    Button(
                        "Stand", id="stand", variant="warning", disabled=not in_progress
                    ),
                ),
                Horizontal(
                    Button(
                        "Double", id="double", variant="success", disabled=not double
                    ),
                    Button("Split", id="split", variant="success", disabled=not split),
                ),
            ),
        )

    def is_valid_bet(self, bet: str) -> bool:
        return (
            int(bet) >= 10
            and int(bet) <= int(self.player.balance / 100)
            and (int(bet) % 10 == 0)
        )


class Game(Container):
    def __init__(self, players: list[Player], num_decks: int) -> None:
        super().__init__()
        self.players = players
        self.shoot = Shoot(decks=num_decks)
        self.in_progress = False
        self.remaining = reactive(len(self.shoot.cards) - self.shoot.reshuffle)
        self.count = reactive(self.shoot.count)

    def compose(self) -> ComposeResult:
        yield Vertical(
            TextContent(Text(f"Cards remaining until reshuffle: {self.remaining}")),
            TextContent(Text(f"Current Count: {self.count}")),
            Section(SectionTitle("Dealer"), CardDisplay(id="dealer_hand")),
            Section(SectionTitle("Players"), Horizontal(id="player_hands")),
            Button("Deal", id="deal", variant="success", disabled=self.in_progress),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "deal":
            self.in_progress = True

            dealer_hand = Hand(dealer=True)
            dealer_cards = self.query_one("#dealer_hand", expect_type=CardDisplay)

            for player in self.players:
                self.query_one("#player_hands").mount(GamePlayer(player))

            dealer_hand.add_card(self.shoot.draw())
            dealer_cards.unicode_hand = f"{dealer_hand.cards[0].unicode()} &#x1F0A0;"

            time.sleep(0.2)

            player_games: list[GamePlayer] = []

            for player in self.players[::-1]:
                player_game = self.query_one("#player_hands", expect_type=GamePlayer)
                player_games.append(player_game)
                player_hand = player_game.hand

                player_hand.add_card(self.shoot.draw())

                player_cards = player_game.query_one(
                    "#player_hand", expect_type=CardDisplay
                )

                player_cards.unicode_hand = " ".join(
                    x.unicode() for x in player_hand.cards
                )
                player_cards.str_hand = str(player_hand)

                time.sleep(0.2)

            for game in player_games:
                player_hand = game.hand
                player_cards = game.query_one("#player_hand", expect_type=CardDisplay)

                player_hand.add_card(self.shoot.draw())
                player_cards.unicode_hand = " ".join(
                    x.unicode() for x in player_hand.cards
                )
                player_cards.str_hand = str(player_hand)
                time.sleep(0.2)


class BlackjackApp(App):
    TITLE = "Blackjack"
    SUB_TITLE = "© Aryan Jain"
    BINDINGS = [
        ("ctrl+t", "toggle_dark", "Toggle dark mode"),
    ]
    CSS_PATH = Path(__file__).parent / "css/style.tcss"

    player_balance = reactive(0)

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
                        CreatePlayer(),
                        # Horizontal(
                        #     Button("Add Player", id="add_player", variant="success"),
                        #     Button(
                        #         "Remove Player", id="remove_player", variant="error"
                        #     ),
                        # ),
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

    def is_valid_bet(self, bet: str) -> bool:
        try:
            return (
                int(bet) >= 10
                and int(bet) <= int(self.player_balance / 100)
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
        if event.button.id == "start_game":
            event.button.disabled = True
            self.player = self.query_one(
                "CreatePlayer", expect_type=CreatePlayer
            ).player

            self.num_decks = self.query_one("#num_decks", expect_type=Input)
            self.shoot = Shoot(decks=int(self.num_decks.value))
            self.cards_remaining = len(self.shoot.cards) - self.shoot.reshuffle

            self.app.query_one(".location-game").scroll_visible(duration=0.5, top=True)

        elif event.button.id == "deal":
            if not self.player:
                return
            else:
                self.player.balance -= (
                    int(self.query_one("#bet", expect_type=Input).value) * 100
                )

                self.dealer_hand = Hand(dealer=True)

                for _ in range(2):
                    self.draw_card(self.player.hand, False)
                    time.sleep(0.2)
                    self.draw_card(self.dealer_hand, True)
                    time.sleep(0.2)

                self.query_one("#hit").disabled = False
                self.query_one("#stand").disabled = False
                self.query_one("#double").disabled = False
                self.query_one("#split").disabled = False
                self.query_one("#surrender").disabled = False

                self.recommended_strategy = STRATEGY.get_strategy(
                    self.player.hand, self.dealer_hand
                )

        elif event.button.id == "hit":
            if not self.player:
                return
            self.draw_card(self.player.hand, False)
            self.query_one("#double").disabled = True
            self.query_one("#split").disabled = True

            self.recommended_strategy = STRATEGY.get_strategy(
                self.player.hand, self.dealer_hand
            )

    def draw_card(self, hand: Hand, dealer: bool) -> None:
        hand.add_card(self.shoot.draw())
        total1, total11 = hand.get_total()
        if dealer:
            self.dealer_unicode = hand.unicode()
            self.dealer_str = str(hand)
            self.dealer_total = str(total11) if total1 <= 21 else "BUST!"
        else:
            self.player_unicode = hand.unicode()
            self.player_str = str(hand)
            if total1 > 21:
                self.player_total = "BUST!"
            else:
                self.player_total = (
                    f"{total1}/{total11}" if total1 != total11 else str(total11)
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
