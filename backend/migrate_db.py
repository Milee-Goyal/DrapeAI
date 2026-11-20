import sqlite3
import os

db_path = r"D:\Project 1 SEM 7\drapeai.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(user_store_accounts)")
existing = [c[1] for c in cursor.fetchall()]

new_cols = [
    ("search_url_template", "VARCHAR(255)"),
    ("badge_color", "VARCHAR(30) DEFAULT '#102C57'"),
    ("is_active", "BOOLEAN DEFAULT 1")
]

for col_name, col_type in new_cols:
    if col_name not in existing:
        cursor.execute(f"ALTER TABLE user_store_accounts ADD COLUMN {col_name} {col_type}")
        print(f"Added column: {col_name}")

conn.commit()
conn.close()
print("Database schema migration successful.")
