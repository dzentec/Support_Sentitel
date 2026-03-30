from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Log, DataTable, Static
from textual.containers import Container, Vertical, Horizontal
import aiosqlite
import asyncio
import os
import json
from datetime import datetime


class SupportTUI(App):
    TITLE = "NEW TUI v3.3"
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]
    CSS = """
        #stats { height: 3; background: $surface; color: $text; }
        .stat-item { padding: 0 1; width: auto; }
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
            id="stats",
        )
        yield Log(id="logs")
        yield DataTable(id="tickets")
        yield Footer()

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
                        "SELECT COUNT(*) FROM tickets WHERE status IN ('awaiting_client', 'closed')"
                    )
                    pending = await db.execute_scalar(
                        "SELECT COUNT(*) FROM tickets WHERE status = 'awaiting_operator'"
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
                        log_widget.write(f"[{timestamp}] {emoji} {level} {event}")
                    except json.JSONDecodeError:
                        log_widget.write(line.strip())


if __name__ == "__main__":
    app = SupportTUI()
    app.run()
