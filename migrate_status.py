import sqlite3


def migrate_status():
    db_path = "data/support.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update statuses
    # New mapping:
    # awaiting_operator -> open
    # awaiting_client -> pending
    # spam_confirmed -> (keep or map to closed? Let's keep for now)

    cursor.execute(
        "UPDATE tickets SET status = 'open' WHERE status = 'awaiting_operator'"
    )
    cursor.execute(
        "UPDATE tickets SET status = 'pending' WHERE status = 'awaiting_client'"
    )

    conn.commit()
    conn.close()
    print("Statuses updated successfully.")


if __name__ == "__main__":
    migrate_status()
