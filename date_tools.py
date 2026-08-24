import datetime

from langchain_core.tools import tool


@tool
def get_today_date() -> str:
    """
    Get today's date in YYYY-MM-DD format.
    """
    return datetime.date.today().isoformat()