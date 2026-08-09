from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def build_calendar_service(creds: Credentials) -> Any:
    """
    Build and return a Google Calendar API resource object.

    Returns:
        A Resource object with methods for interacting with the 
        Google Calendar API.
    """
    service = build("calendar", "v3", credentials=creds)
    return service


def create_event(
    service: Any, 
    title: str,
    start_time: str,
    end_time: str,
    timezone: str = "America/Toronto",
    calendar_id: str = "primary",
) -> None:
    """
    Create a new event in the specified Google Calendar.

    Args:
        service: The Google Calendar API service object.
        title: The title of the event.
        start_time: The start time of the event in RFC3339 format.
        end_time: The end time of the event in RFC3339 format.
        timezone: The timezone for the event (default is "America/Toronto").
        calendar_id: The ID of the calendar to create the event in (default is "primary").
    """
    body = {
        "summary": title,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
    }
    try:
        service.events().insert(calendarId=calendar_id, body=body).execute()
        print("Event created successfully.")
    except Exception as e:
        print(f"An error occurred while creating the event: {e}")