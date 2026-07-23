import sqlite3
from pathlib import Path

DB = Path(r"D:\RunCore3\src\runcore.db")

conn = sqlite3.connect(DB)
cursor = conn.cursor()

print("=" * 90)
print("TABELAS")
print("=" * 90)

tables = cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
AND name NOT LIKE 'sqlite_%'
ORDER BY name
""").fetchall()

for table, in tables:

    print(f"\n{table}")

    cols = cursor.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    for col in cols:

        print(
            f"   {col[1]:25}"
            f"{col[2]:15}"
            f"NULL={not col[3]}"
        )

conn.close()