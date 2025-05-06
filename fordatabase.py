import sqlite3
import pytz
from datetime import datetime

def create_database():
    try:
        # Connect to SQLite database
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Create a function to get Philippine time
        def get_ph_time():
            ph_tz = pytz.timezone('Asia/Manila')
            return datetime.now(ph_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # Register the function with SQLite
        conn.create_function("ph_time", 0, get_ph_time)

        # Create name_tbl
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS name_tbl (
            sr_code TEXT PRIMARY KEY NOT NULL,
            full_name TEXT NOT NULL,
            program TEXT,
            campus TEXT,
            college TEXT
        );
        """)

        # Create time_tbl with Philippine time
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_tbl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sr_code TEXT NOT NULL,
            time_in TEXT DEFAULT (ph_time()),
            date_in TEXT DEFAULT (date(ph_time())),
            FOREIGN KEY (sr_code) REFERENCES name_tbl (sr_code) ON DELETE CASCADE
        );
        """)

        # Add an index for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_tbl_sr_code ON time_tbl (sr_code);")

        conn.commit()
        print("Tables created successfully with Philippine time settings.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"General error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()