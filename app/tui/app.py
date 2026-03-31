import sys
import os

# Fix imports for direct execution by inserting project root at the start of sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Static
from textual.containers import Container, Vertical, Horizontal
import aiosqlite
import asyncio
import os
import json
from datetime import datetime
from app.config import settings


class SupportTUI(App):
    TITLE = "AI Support Sentinel v3.3"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("l", "cycle_log_level", "Cycle Log Level"),
    ]
    CSS = """
        #stats { height: 1; background: $surface; color: $text; }
        .stat-item { padding: 0 1; width: auto; }
        #mode { width: 1fr; text-align: right; }
        #logs { height: 1fr; border: solid $primary; }
        #tickets { height: 1fr; border: solid $secondary; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Static("⏳ Uptime: --", id="uptime", classes="stat-item"),
            Static("📦 Processed: 0", id="processed", classes="stat-item"),
            Static("📤 Sent: 0", id="sent", classes="stat-item"),
            Static("📥 Pending: 0", id="pending", classes="stat-item"),
            Static(f"⚙️ Mode: {settings.LOG_LEVEL}", id="mode", classes="stat-item"),
            id="stats",
        )
        yield Log(id="logs")
        yield DataTable(id="tickets")
        yield Footer()

    def action_cycle_log_level(self) -> None:
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        current = settings.LOG_LEVEL
        next_level = levels[(levels.index(current) + 1) % len(levels)]
        settings.LOG_LEVEL = next_level
        self.query_one("#mode", Static).update(f"⚙️ Mode: {settings.LOG_LEVEL}")
        self.query_one("#logs", Log).write(f"Log level changed to {next_level}\n")

    def on_mount(self) -> None:
        self.start_time = datetime.now()
        self.query_one("#tickets").add_columns("ID", "Status", "Sender")
        self.set_interval(1.0, self.update_header)
        self.set_interval(5.0, self.update_logs)
        self.run_worker(self.update_stats())

    def update_header(self):
        uptime = datetime.now() - self.start_time
        self.query_one("#uptime", Static).update(
            f"⏳ Uptime: {str(uptime).split('.')[0]}"
        )

    async def update_stats(self):
        while True:
            try:
                db_path = os.path.join(os.getcwd(), "data", "support.db")
                async with aiosqlite.connect(db_path) as db:
                    processed = await db.execute_scalar("SELECT COUNT(*) FROM tickets")
                    sent = await db.execute_scalar(
                        "SELECT COUNT(*) FROM tickets WHERE status IN ('pending', 'closed')"
                    )
                    pending = await db.execute_scalar(
                        "SELECT COUNT(*) FROM tickets WHERE status = 'open'"
                    )

                    self.query_one("#processed", Static).update(
                        f"📦 Processed: {processed}"
                    )
                    self.query_one("#sent", Static).update(f"📤 Sent: {sent}")
                    self.query_one("#pending", Static).update(f"📥 Pending: {pending}")
            except Exception as e:
                pass
            await asyncio.sleep(10)

    def update_logs(self):
        log_file = "logs/app.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                lines = f.readlines()[-20:]
                log_widget = self.query_one("#logs", Log)
                log_widget.clear()
                emoji_map = {"INFO": "ℹ️", "DEBUG": "🔍", "ERROR": "❌", "WARNING": "⚠️"}
                for line in lines:
                    try:
                        data = json.loads(line)
                        timestamp = data.get("timestamp", "").replace("T", " ")[:19]
                        level = data.get("log_level", "INFO")
                        event = data.get("event", "")
                        emoji = emoji_map.get(level, "📝")
                        log_widget.write(f"[{timestamp}] {emoji} {level} {event}\n")
                    except json.JSONDecodeError:
                        log_widget.write(line.strip() + "\n")


if __name__ == "__main__":
    app = SupportTUI()
    app.run()
