import datetime
from zoneinfo import ZoneInfo

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan

from auth import get_credentials
from google_client import (
    build_calendar_service,
    get_event as gc_get_event,
    list_events as gc_list_events,
    update_event as gc_update_event,
)

TIMEZONE = ZoneInfo("America/Toronto")


@lifespan
async def calendar_lifespan(server):
    print("Starting calendar service...")
    creds = get_credentials()
    service, error = build_calendar_service(creds)
    if error:
        return

    try:
        yield {
            "service": service,
        }
    finally:
        print("Shutting down calendar service...")
        service.close()


mcp = FastMCP("calendar", lifespan=calendar_lifespan)


@mcp.tool()
def list_day(
    ctx: Context,
    date: datetime.date,
) -> list[dict]:
    """
    List all events for a given date.

    Args:
        date: The date to list events for.

    Returns:
        A list of events. Each event is a dictionary containing the title, 
        start time (HH:MM), end time (HH:MM), and event ID.
    """
    service = ctx.lifespan_context["service"]

    time_min = datetime.datetime.combine(
        date, datetime.time.min, tzinfo=TIMEZONE
    ).isoformat()
    time_max = datetime.datetime.combine(
        date, datetime.time.max, tzinfo=TIMEZONE
    ).isoformat()

    events, error = gc_list_events(service, timeMax=time_max, timeMin=time_min)

    if error:
        raise ToolError(error)

    results = []
    for event in events:
        start_dt = datetime.datetime.fromisoformat(event["start_time"]["dateTime"])
        end_dt = datetime.datetime.fromisoformat(event["end_time"]["dateTime"])

        results.append({
            "title": event["title"],
            "start_time": start_dt.strftime("%H:%M"),
            "end_time": end_dt.strftime("%H:%M"),
            "event_id": event["event_id"],
        })

    return results


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
        start_time: Optional new start time in RFC3339 format.
        end_time: Optional new end time in RFC3339 format.
        reminder_mins: Optional reminder lead time in minutes.
        reminder_method: Optional reminder method (e.g. "popup", "email").

    Returns:
        A dictionary containing the title, start time (HH:MM),
        end time (HH:MM), and event ID.
    """
    service = ctx.lifespan_context["service"]

    error = gc_update_event(
        service=service,
        event_id=event_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        reminder_mins=reminder_mins,
        reminder_method=reminder_method,
    )

    if error:
        raise ToolError(error)

    event, error = gc_get_event(
        service=service,
        event_id=event_id,
    )

    if error:
        raise ToolError(error)

    if not event:
        raise ToolError("Event not found after update")

    start_dt = datetime.datetime.fromisoformat(event["start_time"]["dateTime"])
    end_dt = datetime.datetime.fromisoformat(event["end_time"]["dateTime"])

    return {
        "title": event["title"],
        "start_time": start_dt.strftime("%H:%M"),
        "end_time": end_dt.strftime("%H:%M"),
        "event_id": event["event_id"],
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)