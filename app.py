from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_key_here')

DATABASE = 'database.db'

# ✅ Named columns access
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# ✅ INIT DB
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                security_question TEXT,
                security_answer TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                item TEXT,
                quantity INTEGER
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                item TEXT,
                quantity INTEGER,
                timestamp TEXT
            )
        ''')
        conn.commit()

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        question = request.form['question']
        answer = request.form['answer']
        try:
            conn = get_db()
            conn.execute('INSERT INTO users (username, password, security_question, security_answer) VALUES (?, ?, ?, ?)',
                         (username, password, question, answer))
            conn.commit()
            flash('Signup successful! Please log in.')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Username already taken!')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect('/menu')
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect('/login')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        answer = request.form['answer']
        new_password = request.form['new_password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user and user['security_answer'] == answer:
            hashed_pw = generate_password_hash(new_password)
            conn.execute('UPDATE users SET password = ? WHERE username = ?', (hashed_pw, username))
            conn.commit()
            flash('Password updated! Please log in.')
            return redirect('/login')
        flash('Invalid answer or user!')
    return render_template('forgot_password.html')

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return redirect('/login')
    item = request.form['item']
    quantity = int(request.form['quantity'])
    conn = get_db()
    existing = conn.execute('SELECT * FROM cart WHERE username = ? AND item = ?', (session['username'], item)).fetchone()
    if existing:
        conn.execute('UPDATE cart SET quantity = quantity + ? WHERE username = ? AND item = ?', (quantity, session['username'], item))
    else:
        conn.execute('INSERT INTO cart (username, item, quantity) VALUES (?, ?, ?)', (session['username'], item, quantity))
    conn.commit()
    return redirect('/cart')

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect('/login')
    conn = get_db()
    items = conn.execute('SELECT * FROM cart WHERE username = ?', (session['username'],)).fetchall()
    return render_template('cart.html', items=items)

@app.route('/update-cart', methods=['POST'])
def update_cart():
    item_id = request.form['id']
    quantity = int(request.form['quantity'])
    conn = get_db()
    if quantity <= 0:
        conn.execute('DELETE FROM cart WHERE id = ?', (item_id,))
    else:
        conn.execute('UPDATE cart SET quantity = ? WHERE id = ?', (quantity, item_id))
    conn.commit()
    return redirect('/cart')

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return redirect('/login')
    conn = get_db()
    cart_items = conn.execute('SELECT * FROM cart WHERE username = ?', (session['username'],)).fetchall()
    for item in cart_items:
        conn.execute('INSERT INTO orders (username, item, quantity, timestamp) VALUES (?, ?, ?, ?)',
                     (session['username'], item['item'], item['quantity'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.execute('DELETE FROM cart WHERE username = ?', (session['username'],))
    conn.commit()
    flash('Order placed successfully!')
    return redirect('/menu')

@app.route('/admin')
def admin():
    conn = get_db()
    orders = conn.execute('SELECT * FROM orders ORDER BY timestamp DESC').fetchall()
    return render_template('admin.html', orders=orders)

@app.route('/delete-order/<int:id>')
def delete_order(id):
    conn = get_db()
    conn.execute('DELETE FROM orders WHERE id = ?', (id,))
    conn.commit()
    return redirect('/admin')

@app.route('/edit-order/<int:id>', methods=['GET', 'POST'])
def edit_order(id):
    conn = get_db()
    if request.method == 'POST':
        item = request.form['item']
        quantity = int(request.form['quantity'])
        conn.execute('UPDATE orders SET item = ?, quantity = ? WHERE id = ?', (item, quantity, id))
        conn.commit()
        return redirect('/admin')
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()
    return render_template('edit_order.html', order=order)

# ✅ Create tables when run locally
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
