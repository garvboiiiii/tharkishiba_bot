from datetime import datetime, timedelta

def can_tap(last_tap):
    if not last_tap:
        return True
    return (datetime.utcnow() - last_tap).total_seconds() >= 10800  # 3 hours

def calculate_mining(stake_level):
    hours = 3
    multiplier = {"half": 2, "full": 3}.get(stake_level, 1)
    return 3600 * hours * multiplier  # points earned
