from datetime import datetime, timedelta
from app.tasks.ticket_tasks import get_reminder_trigger


def test_get_reminder_trigger():
    now = datetime.utcnow()
    # 15 min reminder check (interval 15-20)
    assert get_reminder_trigger(now - timedelta(minutes=16)) == 15
    # 30 min reminder check (interval 30-35)
    assert get_reminder_trigger(now - timedelta(minutes=31)) == 30
    # 60 min reminder check (interval 60-65)
    assert get_reminder_trigger(now - timedelta(minutes=61)) == 60
    # No trigger check
    assert get_reminder_trigger(now - timedelta(minutes=5)) is None
    assert get_reminder_trigger(now - timedelta(minutes=20)) is None
    print("All tests passed!")


if __name__ == "__main__":
    test_get_reminder_trigger()
