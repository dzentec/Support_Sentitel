from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable
from textual.containers import Container, Vertical
from textual.timer import Timer
import asyncio
import os


class SupportTUI(App):
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Vertical(
                Log(id="logs", classes="box"),
                DataTable(id="tickets", classes="box"),
                id="main",
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#tickets").add_columns("ID", "Status", "Sender")
        self.set_interval(5.0, self.update_logs)

    def update_logs(self):
        log_file = "/app/logs/app.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = f.readlines()[-20:]
                self.query_one("#logs").clear()
                for line in logs:
                    self.query_one("#logs").write(line)


if __name__ == "__main__":
    app = SupportTUI()
    app.run()
