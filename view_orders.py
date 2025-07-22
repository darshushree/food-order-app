import sqlite3

conn = sqlite3.connect('orders.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM orders")
rows = cursor.fetchall()

print("📦 All Orders:")
for row in rows:
    print(row)

conn.close()
