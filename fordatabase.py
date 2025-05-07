import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('attendance.db')
cursor = conn.cursor()

# Delete all records from the tables
cursor.execute("DELETE FROM time_tbl")
cursor.execute("DELETE FROM name_tbl")

# Commit changes and close the connection
conn.commit()
conn.close()
