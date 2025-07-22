
import sqlite3

conn = sqlite3.connect('orders.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    qty INTEGER NOT NULL
)
''')

conn.commit()
conn.close()

print("✅ orders.db created and table updated.")
