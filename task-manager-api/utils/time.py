from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

def parse_date(value):
    if not value: return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Formato de data inválido. Use ISO-8601") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

def is_overdue(value, status):
    if not value or status in {"done", "cancelled"}: return False
    if value.tzinfo is None: value = value.replace(tzinfo=timezone.utc)
    return value < utc_now()
