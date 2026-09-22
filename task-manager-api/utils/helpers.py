from datetime import timezone
from utils.time import utc_now, parse_date

def format_date(value):
    if not value: return None
    return value.isoformat() if hasattr(value, 'isoformat') else str(value)

def calculate_percentage(part, total):
    return round(part / total * 100, 2) if total else 0

def validate_email(email):
    from utils.validation import EMAIL_RE
    return bool(isinstance(email, str) and EMAIL_RE.match(email))

def parse_utc_date(value):
    return parse_date(value)

def log_action(action, details=None):
    # Keep operational logging free of passwords and tokens.
    print(f"[{utc_now().isoformat()}] {action}")
