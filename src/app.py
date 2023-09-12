from pathlib import Path
from typing import Optional

from rich.markdown import Markdown
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from classes import (
    AboveFold,
    Body,
    Column,
    Player,
    QuickAccess,
    Section,
    SectionTitle,
    Shoot,
    Strategy,
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
                TextContent(Text("Name: ")),
                Input("Name", name="name"),
                TextContent(Text("Buy In: ")),
                Input("Buy In", name="buy_in"),
            ),
            Button("Create", id="create_player", variant="success"),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_player":
            name = self.query_one("Input[name='name']", expect_type=Input).value
            buy_in = self.query_one("Input[name='buy_in']", expect_type=Input).value
            self.player = Player(name=name, balance=int(buy_in) * 100)

            # self.app.query_one(".location-play").scroll_visible(duration=0.5, top=True)


class Game(Container):
    def __init__(self, players: list[Player], num_decks: int) -> None:
        super().__init__()
        self.players = players
        self.shoot = Shoot(decks=num_decks)

    def compose(self) -> ComposeResult:
        yield Static(Markdown(WELCOME))


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
                        Button("Start Game", id="start_game", variant="warning"),
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

            self.app.query_one(".location-play").scroll_visible(duration=0.5, top=True)

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
