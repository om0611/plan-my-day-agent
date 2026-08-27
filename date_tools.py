import datetime
from zoneinfo import ZoneInfo

from langchain_core.tools import ToolException, tool


@tool
def get_datetime_context(timezone: str) -> dict:
    """
    Get the current date and time for a given IANA timezone.

    Args:
        timezone: IANA timezone string (e.g. 'America/Toronto').

    Returns:
        A dictionary with:
            - date: today's date in YYYY-MM-DD format.
            - time: current local time in HH:MM format.
    """
    try:
        tz = ZoneInfo(timezone)
    except Exception as e:
        raise ToolException(f"Invalid timezone '{timezone}': {e}") from e

    now = datetime.datetime.now(tz)
    return {
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M"),
    }


@tool
def format_to_rfc3339(date: str, time: str, timezone: str) -> str:
    """
    Format a given date, time, and IANA timezone into an RFC3339 timestamp string.

    Args:
        date: Date in YYYY-MM-DD format (e.g. "2026-08-24").
        time: Time in HH:MM format (e.g. "14:30").
        timezone: IANA timezone string (e.g. "America/Toronto").

    Returns:
        RFC3339 formatted timestamp string (e.g. "2026-08-24T14:30:00-04:00").
    """
    try:
        tz = ZoneInfo(timezone)
    except Exception as e:
        raise ToolException(f"Invalid timezone '{timezone}': {e}") from e

    try:
        d = datetime.date.fromisoformat(date)
    except Exception as e:
        raise ToolException(f"Invalid date '{date}'. Expected YYYY-MM-DD format: {e}") from e

    try:
        t = datetime.time.fromisoformat(time)
    except Exception as e:
        raise ToolException(f"Invalid time '{time}'. Expected HH:MM format: {e}") from e

    dt = datetime.datetime.combine(d, t, tzinfo=tz)
    return dt.isoformat()

