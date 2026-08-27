import datetime


def parse_utc_offset(utc_offset: str) -> datetime.timezone:
    """Parse a UTC offset string (e.g. '-0400', '-04:00', '+0530', 'Z') into datetime.timezone."""
    offset_str = utc_offset.strip().upper()
    if offset_str in ("Z", "UTC", "+0000", "+00:00", "-0000", "-00:00"):
        return datetime.timezone.utc

    clean = offset_str.replace(":", "")
    sign = -1 if clean.startswith("-") else 1
    digits = clean.lstrip("+-")
    if not digits or not digits.isdigit():
        raise ValueError(f"Invalid offset format: '{utc_offset}'")
    hours = int(digits[:2]) if len(digits) >= 2 else int(digits)
    minutes = int(digits[2:4]) if len(digits) >= 4 else 0
    if hours > 23 or minutes > 59:
        raise ValueError(f"Offset out of range: '{utc_offset}'")
    return datetime.timezone(datetime.timedelta(hours=sign * hours, minutes=sign * minutes))

