import sqlite3

connection = sqlite3.connect(
    r"D:\RunCore3\src\runcore.db"
)

row = connection.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name = 'strava_connections'
    """
).fetchone()

print(row)

connection.close()