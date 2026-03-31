import sqlite3


def migrate():
    db_path = "data/support.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Добавляем колонку, если ее нет
        cursor.execute(
            "ALTER TABLE tickets ADD COLUMN reminders_sent_intervals TEXT DEFAULT ''"
        )
        conn.commit()
        print("Миграция прошла успешно: колонка 'reminders_sent_intervals' добавлена.")
    except sqlite3.OperationalError as e:
        print(f"Ошибка (возможно, колонка уже существует или база не найдена): {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
