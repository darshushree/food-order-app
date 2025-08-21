import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('orders.db')
c = conn.cursor()

# ✅ Create orders table
c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    qty INTEGER NOT NULL
)
''')

# ✅ Create users table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# ✅ Ensure admin user exists
admin = c.execute("SELECT * FROM users WHERE username = 'admin'").fetchone()
if not admin:
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              ('admin', generate_password_hash('admin123')))
    print("👑 Default admin created → username: admin | password: admin123")
else:
    print("✅ Admin user already exists")

conn.commit()
conn.close()

print("✅ orders.db created and tables updated.")
