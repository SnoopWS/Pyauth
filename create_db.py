import sqlite3

# Connect to the existing database
conn = sqlite3.connect('mydatabase.db')
cursor = conn.cursor()

# Create a new table for 'app_secrets' with the desired schema
cursor.execute('''
    CREATE TABLE IF NOT EXISTS app_secrets (
        app_name TEXT PRIMARY KEY NOT NULL,
        secret_key TEXT NOT NULL,
        username TEXT  -- Add the 'username' column here
    )
''')

# Create a new table for 'license_keys' with the desired schema
cursor.execute('''
    CREATE TABLE IF NOT EXISTS license_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL,
        plan TEXT NOT NULL,
        expiry_date DATE NOT NULL,
        application TEXT NOT NULL,
        hwid TEXT,
        hwid_last_updated DATE
    )
''')

# Commit the changes and close the database connection
conn.commit()
conn.close()

print("Success")
