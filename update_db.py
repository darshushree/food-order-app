import sqlite3

# Connect to your SQLite database
  
conn = sqlite3.connect('orders.db')# replace with your actual DB name
  
cursor = conn.cursor()

# Add the new columns for password reset
try:
    cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT;")
    cursor.execute("ALTER TABLE users ADD COLUMN security_answer TEXT;")
    print("✅ Columns added successfully!")
except Exception as e:
    print("⚠️ Error:", e)

conn.commit()
conn.close()
