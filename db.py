import sqlite3

from langchain_core.tools import ToolException


DB_PATH = "schedule.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Get a new database connection.

    Returns:
        sqlite3.Connection: The database connection.
    """
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        raise ToolException(f"Error connecting to database: {e}") from e


def close_db_connection(conn: sqlite3.Connection):
    """
    Close the database connection.
    
    Args:
        conn: The database connection.
    """
    try:
        conn.close()
    except sqlite3.Error as e:
        raise ToolException(f"Error closing database connection: {e}") from e


def init_db(conn: sqlite3.Connection):
    """
    Initialize the database tables.
    
    Args:
        conn: The database connection.
    """
    try:
        cur = conn.cursor()

        # Create the tables
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                priority INTEGER NOT NULL CHECK (priority >= 1 AND priority <= 10)
            );

            CREATE TABLE IF NOT EXISTS days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fixed_activities (
                activity_id INTEGER NOT NULL,
                day_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                
                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                FOREIGN KEY (day_id) REFERENCES days(id) ON DELETE CASCADE,
                PRIMARY KEY (activity_id, day_id, start_time, end_time)
            );

            CREATE TABLE IF NOT EXISTS budget_activities (
                activity_id INTEGER NOT NULL,
                day_ids TEXT NOT NULL,
                hours REAL NOT NULL,

                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
                PRIMARY KEY (activity_id, day_ids)
            );

            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_id INTEGER UNIQUE NOT NULL,
                anchor_date TEXT NOT NULL,

                FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS cycle_slots (
                cycle_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                label TEXT NOT NULL,

                FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
                PRIMARY KEY (cycle_id, position)
            );
        """)
        conn.commit()

        # Initialize days table with all days of the week
        days = [
            ("Monday",), 
            ("Tuesday",), 
            ("Wednesday",), 
            ("Thursday",), 
            ("Friday",), 
            ("Saturday",), 
            ("Sunday",)
        ]
        cur.executemany("INSERT OR IGNORE INTO days (day) VALUES (?)", days)
        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise


def add_activity(conn: sqlite3.Connection, name: str, priority: int):
    """
    Add a new activity to the database.
    
    Args:
        name: The name of the activity.
        priority: The priority of the activity (1-10). Higher value means higher priority.
    """
    if not (1 <= priority <= 10):
        raise ValueError("Priority must be between 1 and 10.")
    
    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO activities (name, priority) 
            VALUES (?, ?)
        """, (name, priority))

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise ToolException(f"Error adding activity: {e}") from e


def update_activity(conn: sqlite3.Connection, name: str, new_name: str = None, new_priority: int = None):
    """
    Update an existing activity in the database.
    
    Args:
        name: The current name of the activity to update.
        new_name: The new name for the activity (optional).
        new_priority: The new priority for the activity (optional, 1-10).
    """
    if new_name is None and new_priority is None:
        raise ValueError("At least one of new_name or new_priority must be provided.")

    if new_priority is not None and not (1 <= new_priority <= 10):
        raise ValueError("Priority must be between 1 and 10.")

    try:
        cur = conn.cursor()

        if new_name is not None and new_priority is not None:
            cur.execute("""
                UPDATE activities 
                SET name = ?, priority = ? 
                WHERE name = ?
            """, (new_name, new_priority, name))

        elif new_name is not None:
            cur.execute("""
                UPDATE activities 
                SET name = ? 
                WHERE name = ?
            """, (new_name, name))
        
        else:
            cur.execute("""
                UPDATE activities 
                SET priority = ? 
                WHERE name = ?
            """, (new_priority, name))

        if cur.rowcount == 0:
            raise ToolException(f"Activity '{name}' not found.")

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise ToolException(f"Error updating activity: {e}") from e


def delete_activity(conn: sqlite3.Connection, name: str):
    """
    Delete an activity from the database.
    
    Args:
        name: The name of the activity to delete.
    """
    try:
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM activities 
            WHERE name = ?
        """, (name,))

        if cur.rowcount == 0:
            raise ToolException(f"Activity '{name}' not found.")

        conn.commit()

    except sqlite3.Error as e:
        conn.rollback()
        raise ToolException(f"Error deleting activity: {e}") from e


def list_activities(conn: sqlite3.Connection):
    """
    List all activities in the database.
    
    Returns:
        A list containing (activity name, priority) tuples.
    """
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT name, priority 
            FROM activities
            ORDER BY priority DESC
        """)

        return cur.fetchall()

    except sqlite3.Error as e:
        raise ToolException(f"Error listing activities: {e}") from e


if __name__ == "__main__":
    conn = get_db_connection()
    init_db(conn)
    close_db_connection(conn)