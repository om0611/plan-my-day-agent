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