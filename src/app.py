from pathlib import Path
from typing import Optional

from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
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
            Horizontal(
                Label("Name: "),
                Input("Name", name="name"),
                Label("Buy In: "),
                Input("Buy In", name="buy_in"),
            ),
            Button(
                "Create",
                id="create_player",
                variant="success",
                disabled=self.player is not None,
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_player":
            name = self.query_one("Input[name='name']", expect_type=Input).value
            buy_in = self.query_one("Input[name='buy_in']", expect_type=Input).value
            self.player = Player(name=name, balance=int(buy_in) * 100)

            # self.app.query_one(".location-play").scroll_visible(duration=0.5, top=True)


class GamePlayer(Container):
    def __init__(self, player: Player) -> None:
        super().__init__()
        self.player = player
        self.hand = Hand()

    def compose(self) -> ComposeResult:
        in_progress = self.app.query_one("#game", expect_type=Game).in_progress

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
            CardDisplay(self.hand),
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


class CardDisplay(Container):
    def __init__(self, hand: Hand) -> None:
        super().__init__()
        self.hand = hand

    def compose(self) -> ComposeResult:
        if self.hand.dealer:
            unicode_hand = f"{self.hand.cards[0].unicode()} &#x1F0A0;"
        else:
            unicode_hand = " ".join(x.unicode() for x in self.hand.cards)

        yield Vertical(
            TextContent(Markdown(unicode_hand), classes="hand", id="hand"),
            SubTitle(str(self.hand)),
        )


class Game(Container):
    def __init__(self, players: list[Player], num_decks: int) -> None:
        super().__init__()
        self.players = players
        self.shoot = Shoot(decks=num_decks)
        self.in_progress = False

    def compose(self) -> ComposeResult:
        remaining = len(self.shoot.cards) - self.shoot.reshuffle

        yield Vertical(
            TextContent(Text(f"Cards remaining until reshuffle: {remaining}")),
            TextContent(Text(f"Current Count: {self.shoot.count}")),
            Section(SectionTitle("Dealer"), Container()),
            Button("Deal", id="deal", variant="success", disabled=self.in_progress),
        )


class BlackjackApp(App):
    TITLE = "Blackjack"
    SUB_TITLE = "© Aryan Jain"
    BINDINGS = [
        ("ctrl+t", "toggle_dark", "Toggle dark mode"),
    ]
    CSS_PATH = Path(__file__).parent / "css/style.tcss"

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
                        DataTable(id="splits"),
                        TextContent(Text("Surrender", style="bold")),
                        DataTable(id="surrender"),  # type: ignore
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
                        Container(CreatePlayer(), id="players"),
                        Horizontal(
                            Button("Add Player", id="add_player", variant="success"),
                            Button(
                                "Remove Player", id="remove_player", variant="error"
                            ),
                        ),
                        Input(
                            placeholder="Number of Decks",
                            name="num_decks",
                            validators=[Number(minimum=1, maximum=8)],
                        ),
                        Pretty([]),
                        Button("Start Game", id="start_game", variant="warning"),
                    ),
                    Section(
                        SectionTitle("Game"),
                        Container(id="game"),
                    ),
                    classes="location-play",
                ),
            ),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_player":
            self.query_one("#players").mount(CreatePlayer())
        elif event.button.id == "remove_player":
            players = self.query("#players")
            if players:
                players.last().remove()
        elif event.button.id == "start_game":
            players = self.query("#players")
            self.players = []
            if players:
                for player in players:
                    create_player = player.query_one(
                        "Container", expect_type=CreatePlayer
                    )
                    if create_player.player:
                        self.players.append(create_player.player)

            num_decks = self.query_one("Input[name='num_decks']", expect_type=Input)

            self.query_one("#game").mount(
                Game(players=self.players, num_decks=int(num_decks.value))
            )

            self.app.query_one(".location-play").scroll_visible(duration=0.5, top=True)

    @on(Input.Changed)
    def show_invalid_reasons(self, event: Input.Changed) -> None:
        # Updating the UI to show the reasons why validation failed
        if event.input.id == "num_decks":
            if event.validation_result and not event.validation_result.is_valid:
                self.query_one(Pretty).update(
                    event.validation_result.failure_descriptions
                )
            else:
                self.query_one(Pretty).update([])

    def on_mount(self) -> None:
        lookup = {
            "hard-totals": STRATEGY.hard_totals,
            "soft-totals": STRATEGY.soft_totals,
            "splits": STRATEGY.splits,
        }

        for strategy in ["hard-totals", "soft-totals", "splits", "surrender"]:
            match strategy:
                case "surrender":
                    table: DataTable = self.app.query_one(
                        "#surrender", expect_type=DataTable
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
