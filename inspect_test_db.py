from pathlib import Path
import sqlite3

database_path = Path("db_repair_test.sqlite3").resolve()
connection = sqlite3.connect(database_path)

print("Test database:", database_path)
print("Tables:")
for row in connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
):
    print("-", row[0])

connection.close()
