import datetime
from zoneinfo import ZoneInfo

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan

from auth import get_credentials
from google_client import (
    build_calendar_service,
    create_event as gc_create_event,
    delete_event as gc_delete_event,
    get_event as gc_get_event,
    get_user_timezone,
    list_events as gc_list_events,
    update_event as gc_update_event,
)


def format_event(event: dict) -> dict:
    """Safely format an event dictionary, handling both timed and all-day events."""
    start = event.get("start_time") or {}
    end = event.get("end_time") or {}

    if "dateTime" in start and start["dateTime"]:
        start_dt = datetime.datetime.fromisoformat(start["dateTime"])
        start_str = start_dt.strftime("%Y-%m-%d %H:%M")
    elif "date" in start and start["date"]:
        start_str = f"{start['date']} (all-day)"
    else:
        start_str = "N/A"

    if "dateTime" in end and end["dateTime"]:
        end_dt = datetime.datetime.fromisoformat(end["dateTime"])
        end_str = end_dt.strftime("%Y-%m-%d %H:%M")
    elif "date" in end and end["date"]:
        end_str = f"{end['date']} (all-day)"
    else:
        end_str = "N/A"

    return {
        "title": event.get("title") or "(No title)",
        "start_time": start_str,
        "end_time": end_str,
        "event_id": event.get("event_id"),
    }


@lifespan
async def calendar_lifespan(server):
    print("Starting calendar service...")
    creds = get_credentials()
    try:
        service = build_calendar_service(creds)
        timezone = get_user_timezone(service)
        print(f"User timezone: {timezone}")
    except Exception as e:
        print(f"Failed to build calendar service: {e}")
        return

    try:
        yield {
            "service": service,
            "timezone": timezone,
        }
    finally:
        print("Shutting down calendar service...")
        service.close()


mcp = FastMCP("calendar", lifespan=calendar_lifespan)


@mcp.tool()
def get_timezone(ctx: Context) -> str:
    """
    Get the user's timezone as an IANA timezone string (e.g. 'America/Toronto').
    """
    return ctx.lifespan_context["timezone"]


@mcp.tool()
def list_day(
    ctx: Context,
    date: str,
    timezone: str,
) -> list[dict]:
    """
    List all events for a given date.

    Args:
        date: The date to list events for in YYYY-MM-DD format (e.g. "2026-08-24").
        timezone: The user's IANA timezone string (e.g. "America/Toronto").

    Returns:
        A list of events. Each event is a dictionary containing the title, 
        start time (YYYY-MM-DD HH:MM), end time (YYYY-MM-DD HH:MM), and event ID.
    """
    service = ctx.lifespan_context["service"]

    try:
        tz = ZoneInfo(timezone)
    except Exception as e:
        raise ToolError(f"Invalid timezone '{timezone}': {e}") from e

    try:
        d = datetime.date.fromisoformat(date)
    except Exception as e:
        raise ToolError(f"Invalid date '{date}'. Expected YYYY-MM-DD format: {e}") from e

    try:
        time_min = datetime.datetime.combine(
            d, datetime.time.min, tzinfo=tz
        ).isoformat()
        time_max = datetime.datetime.combine(
            d, datetime.time.max, tzinfo=tz
        ).isoformat()

        events = gc_list_events(service, timeMax=time_max, timeMin=time_min)
        return [format_event(event) for event in events]
    except Exception as e:
        raise ToolError(f"Failed to list events: {e}") from e


@mcp.tool()
def update_event(
    ctx: Context,
    event_id: str,
    title: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    reminder_mins: int | None = None,
    reminder_method: str | None = None,
) -> dict:
    """
    Update an existing event.

    Args:
        event_id: The ID of the event to update.
        title: Optional new title for the event.
        start_time: Optional new start time in RFC3339 format (e.g. "2026-08-24T14:30:00-04:00").
        end_time: Optional new end time in RFC3339 format (e.g. "2026-08-24T15:30:00-04:00").
        reminder_mins: Optional reminder lead time in minutes.
        reminder_method: Optional reminder method (e.g. "popup", "email").

    Returns:
        A dictionary containing the title, start time (YYYY-MM-DD HH:MM),
        end time (YYYY-MM-DD HH:MM), and event ID of the updated event.
    """
    service = ctx.lifespan_context["service"]

    try:
        gc_update_event(
            service=service,
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            reminder_mins=reminder_mins,
            reminder_method=reminder_method,
        )
        event = gc_get_event(
            service=service,
            event_id=event_id,
        )
        return format_event(event)
    except Exception as e:
        raise ToolError(f"Failed to update event: {e}")


@mcp.tool()
def create_event(
    ctx: Context,
    title: str,
    start_time: str,
    end_time: str,
    reminder_mins: int = 5,
    reminder_method: str = "popup",
) -> dict:
    """
    Create a new calendar event.

    Args:
        title: The title of the event.
        start_time: The start time of the event in RFC3339 format (e.g. "2026-08-24T14:30:00-04:00").
        end_time: The end time of the event in RFC3339 format (e.g. "2026-08-24T15:30:00-04:00").
        reminder_mins: Minutes before the event to send a reminder (default 5).
        reminder_method: Reminder method, e.g. "popup" or "email" (default "popup").

    Returns:
        A dictionary containing the title, start time (YYYY-MM-DD HH:MM),
        end time (YYYY-MM-DD HH:MM), and event ID of the created event.
    """
    service = ctx.lifespan_context["service"]

    try:
        event_id = gc_create_event(
            service=service,
            title=title,
            start_time=start_time,
            end_time=end_time,
            reminder_mins=reminder_mins,
            reminder_method=reminder_method,
        )
        event = gc_get_event(
            service=service,
            event_id=event_id,
        )
        return format_event(event)
    except Exception as e:
        raise ToolError(f"Failed to create event: {e}")


@mcp.tool()
def get_event(
    ctx: Context,
    event_id: str,
) -> dict:
    """
    Get details of a calendar event by its ID.

    Args:
        event_id: The ID of the event to retrieve.

    Returns:
        A dictionary containing the title, start time (YYYY-MM-DD HH:MM),
        end time (YYYY-MM-DD HH:MM), and event ID of the event.
    """
    service = ctx.lifespan_context["service"]

    try:
        event = gc_get_event(
            service=service,
            event_id=event_id,
        )
        return format_event(event)
    except Exception as e:
        raise ToolError(f"Failed to get event: {e}")


@mcp.tool()
def delete_event(
    ctx: Context,
    event_id: str,
) -> None:
    """
    Delete a calendar event by its ID.

    Args:
        event_id: The ID of the event to delete.

    Returns:
        None on success, or raises a ToolError if an error occurred.
    """
    service = ctx.lifespan_context["service"]

    try:
        gc_delete_event(
            service=service,
            event_id=event_id,
        )
    except Exception as e:
        raise ToolError(f"Failed to delete event: {e}")


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)