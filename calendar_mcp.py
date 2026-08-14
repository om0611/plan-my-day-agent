import datetime
from zoneinfo import ZoneInfo

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.server.lifespan import lifespan

from auth import get_credentials
from google_client import (
    build_calendar_service,
    create_event,
    delete_event,
    update_event,
    get_event,
    list_events,
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
    date: datetime.date = datetime.datetime.now().date()
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

    time_min = datetime.datetime.combine(date, datetime.time.min, tzinfo=TIMEZONE).isoformat()
    time_max = datetime.datetime.combine(date, datetime.time.max, tzinfo=TIMEZONE).isoformat()

    events, error = list_events(service, timeMax=time_max, timeMin=time_min)

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


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)