from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def build_calendar_service(creds: Credentials) -> Any:
    """
    Build and return a Google Calendar API resource object.

    Returns:
        A Resource object with methods for interacting with the
        Google Calendar API. None if an error occured.
    """
    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except Exception as e:
        print(f"An error occurred while building the calendar service: {e}")
        return None


def create_event(
    service: Any,
    title: str,
    start_time: str,
    end_time: str,
    timezone: str = "America/Toronto",
    reminder_mins: int = 5,
    reminder_method: str = "popup",
    calendar_id: str = "primary",
) -> str | None:
    """
    Create a new event in the specified Google Calendar.

    Args:
        service: The Google Calendar API service object.
        title: The title of the event.
        start_time: The start time of the event in RFC3339 format.
        end_time: The end time of the event in RFC3339 format.
        timezone: The timezone for the event (default is "America/Toronto").
        reminder_mins: The number of minutes before the event to send a reminder
            (default is 5).
        reminder_method: The method to use for the reminder (default is "popup").
            Possible values: "popup", "email".
        calendar_id: The ID of the calendar to create the event in (default is
            "primary").

    Returns:
        The ID of the created event if successful, None otherwise.
    """
    body = {
        "summary": title,
        "start": {"dateTime": start_time, "timeZone": timezone},
        "end": {"dateTime": end_time, "timeZone": timezone},
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": reminder_method, "minutes": reminder_mins}],
        },
    }
    try:
        response = service.events().insert(calendarId=calendar_id, body=body).execute()
        print("Event created successfully.")
        return response.get("id")

    except Exception as e:
        print(f"An error occurred while creating the event: {e}")
        return None


def delete_event(
    service: Any,
    event_id: str,
    calendar_id: str = "primary",
) -> None:
    """
    Delete an event from the specified Google Calendar.

    Args:
        service: The Google Calendar API service object.
        event_id: The ID of the event to delete.
        calendar_id: The ID of the calendar to delete the event from (default is
            "primary").
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print("Event deleted successfully.")

    except Exception as e:
        print(f"An error occurred while deleting the event: {e}")


def update_event(
    service: Any,
    event_id: str,
    title: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    timezone: str = "America/Toronto",
    reminder_mins: int | None = None,
    reminder_method: str | None = None,
    calendar_id: str = "primary",
) -> None:
    """
    Update an existing event in the specified Google Calendar with partial fields.

    Args:
        service: The Google Calendar API service object.
        event_id: The ID of the event to update.
        title: Optional new title for the event.
        start_time: Optional new start time in RFC3339 format.
        end_time: Optional new end time in RFC3339 format.
        timezone: Timezone for start/end times (default "America/Toronto").
        reminder_mins: Optional reminder lead time in minutes.
        reminder_method: Optional reminder method (e.g. "popup", "email").
        calendar_id: The ID of the calendar containing the event (default "primary").
    """
    body: dict[str, Any] = {}

    if title is not None:
        body["summary"] = title

    if start_time is not None:
        body["start"] = {"dateTime": start_time, "timeZone": timezone}

    if end_time is not None:
        body["end"] = {"dateTime": end_time, "timeZone": timezone}

    if reminder_mins is not None or reminder_method is not None:
        body["reminders"] = {
            "useDefault": False,
            "overrides": [
                {
                    "method": reminder_method or "popup",
                    "minutes": reminder_mins if reminder_mins is not None else 5,
                }
            ],
        }

    if not body:
        print("No fields provided to update.")
        return

    try:
        service.events().patch(
            calendarId=calendar_id, eventId=event_id, body=body
        ).execute()
        print("Event updated successfully.")

    except Exception as e:
        print(f"An error occurred while updating the event: {e}")


def list_events(
    service: Any,
    timeMax: str,
    timeMin: str,
    calendar_id: str = "primary",
) -> list:
    """
    List events from the specified Google Calendar within the given time range.

    Args:
        service: The Google Calendar API service object.
        timeMax: The maximum time for the event (in RFC3339 format).
        timeMin: The minimum time for the event (in RFC3339 format).
        calendar_id: The ID of the calendar to list events from (default "primary").

    Returns:
        A list of events from the specified calendar.
    """
    try:
        response = service.events().list(
            calendarId=calendar_id,
            timeMin=timeMin,
            timeMax=timeMax,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = response.get("items")
        if not events:
            print("No events found.")
            return []

        output_events = []

        for event in events:
            title = event.get("summary")
            start_time = event.get("start")
            end_time = event.get("end")
            event_id = event.get("id")

            output_events.append(
                {
                    "title": title,
                    "start_time": start_time,
                    "end_time": end_time,
                    "event_id": event_id,
                }
            )

        return output_events

    except Exception as e:
        print(f"An error occurred while listing events: {e}")
        return []