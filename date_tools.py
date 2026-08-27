import datetime

from langchain_core.tools import ToolException, tool

from date_helpers import parse_utc_offset


@tool
def get_datetime_context() -> dict:
    """
    Get the current date, time, and the user's UTC offset.

    Returns:
        A dictionary with:
            - date: today's date in YYYY-MM-DD format.
            - time: current local time in HH:MM format.
            - utc_offset: the user's UTC offset in ±HHMM format (e.g. "-0400", "+0530").
    """
    now = datetime.datetime.now().astimezone()
    return {
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
        "utc_offset": now.strftime("%z"),
    }


@tool
def format_to_rfc3339(date: str, time: str, utc_offset: str) -> str:
    """
    Format a given date, time, and UTC offset into an RFC3339 timestamp string.

    Args:
        date: Date in YYYY-MM-DD format (e.g. "2026-08-24").
        time: Time in HH:MM format (e.g. "14:30").
        utc_offset: UTC offset in ±HHMM or ±HH:MM format (e.g. "-0400", "-04:00").

    Returns:
        RFC3339 formatted timestamp string (e.g. "2026-08-24T14:30:00-04:00").
    """
    try:
        tz = parse_utc_offset(utc_offset)
    except Exception as e:
        raise ToolException(str(e))

    try:
        d = datetime.date.fromisoformat(date)
    except Exception as e:
        raise ToolException(f"Invalid date '{date}'. Expected YYYY-MM-DD format: {e}")

    try:
        t = datetime.time.fromisoformat(time)
    except Exception as e:
        raise ToolException(f"Invalid time '{time}'. Expected HH:MM format: {e}")

    dt = datetime.datetime.combine(d, t, tzinfo=tz)
    return dt.isoformat()
