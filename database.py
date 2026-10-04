import sqlite3

connection = sqlite3.connect("volunteer.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS volunteers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    skills TEXT,
    availability TEXT
)
""")

connection.commit()
connection.close()

print("Database created successfully!")