import sys
import os
import time

# Добавим вывод времени изменения файла
mtime = os.path.getmtime(__file__)
print(f"DEBUG: File modified at: {time.ctime(mtime)}")

with open("tui_debug.log", "w") as f:
    f.write(f"TUI loaded from: {__file__}\n")
    f.write(f"Python executable: {sys.executable}\n")
    f.write(f"Current Working Directory: {os.getcwd()}\n")
    f.write(f"sys.path: {sys.path}\n")

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Static
from textual.containers import Container, Vertical, Horizontal
import aiosqlite
import asyncio
import json
from datetime import datetime


class SupportTUI(App):
    TITLE = "NEW TUI v3.3"
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]

    CSS = """
        #stats { height: 3; dock: top; background: $surface; padding: 0 1; }
        .stat-item { padding: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("Uptime: --", id="uptime"),
            Static("Processed: 0", id="processed"),
            Static("Sent: 0", id="sent"),
            Static("Pending: 0", id="pending"),
            id="stats",
        )
        yield Container(
            Vertical(
                Log(id="logs", classes="box"),
                DataTable(id="tickets", classes="box"),
                id="main",
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        self.start_time = datetime.now()
        self.query_one("#tickets").add_columns("ID", "Status", "Sender")
        self.set_interval(1.0, self.update_header)
        self.set_interval(5.0, self.update_logs)
        self.run_worker(self.update_stats())

    def update_header(self):
        uptime = datetime.now() - self.start_time
        self.query_one("#uptime", Static).update(f"Uptime: {str(uptime).split('.')[0]}")

    async def update_stats(self):
        while True:
            try:
                async with aiosqlite.connect("data/support.db") as db:
                    processed = await db.execute_scalar("SELECT COUNT(*) FROM tickets")
                    sent = await db.execute_scalar(
                        "SELECT COUNT(*) FROM tickets WHERE status IN ('awaiting_client', 'closed')"
                    )
                    pending = await db.execute_scalar(
                        "SELECT COUNT(*) FROM tickets WHERE status = 'awaiting_operator'"
                    )

                    self.query_one("#processed", Static).update(
                        f"Processed: {processed}"
                    )
                    self.query_one("#sent", Static).update(f"Sent: {sent}")
                    self.query_one("#pending", Static).update(f"Pending: {pending}")
            except Exception as e:
                pass  # Silent fail for TUI stats
            await asyncio.sleep(10)

    def update_logs(self):
        log_file = "logs/app.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()[-20:]
                log_widget = self.query_one("#logs", Log)
                log_widget.clear()
                for line in lines:
                    try:
                        data = json.loads(line)
                        timestamp = data.get("timestamp", "").replace("T", " ")[:19]
                        level = data.get("log_level", "INFO")
                        event = data.get("event", "")
                        log_widget.write(f"[{timestamp}] [{level}] {event}")
                    except json.JSONDecodeError:
                        log_widget.write(line.strip())


if __name__ == "__main__":
    app = SupportTUI()
    app.run()
