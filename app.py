from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = '7d9f8s7g8sdfg878sf878sdfg978sdf987'

# ✅ Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn

# ✅ Auto-create Tables on Startup
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            security_question TEXT,
            security_answer TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            qty INTEGER NOT NULL
        )
    ''')
    # Optional: Insert default user
    user = conn.execute('SELECT * FROM users WHERE username = ?', ('testuser',)).fetchone()
    if not user:
        conn.execute(
            'INSERT INTO users (username, password_hash, security_question, security_answer) VALUES (?, ?, ?, ?)',
            ('testuser', generate_password_hash('test123'), 'Your favorite food?', 'Pizza')
        )
    conn.commit()
    conn.close()

init_db()

# ✅ Splash Screen Route (FIRST PAGE)
@app.route('/')
def splash():
    return render_template('splash.html')

# ✅ Home Page
@app.route('/home')
def home():
    return render_template('home.html')

# ✅ Menu Page
@app.route('/menu')
def menu():
    return render_template('menu.html')

# ✅ Order Page
@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        item = request.form['item']
        qty = request.form['qty']

        conn = get_db_connection()
        conn.execute('INSERT INTO orders (item, qty) VALUES (?, ?)', (item, qty))
        conn.commit()
        conn.close()

        return render_template('confirmation.html', item=item, qty=qty)
    return render_template('order.html')

# ✅ SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer']

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password_hash, security_question, security_answer) VALUES (?, ?, ?, ?)',
                (username, password_hash, security_question, security_answer)
            )
            conn.commit()
            conn.close()
            flash('Account created successfully! Please log in.')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('Username already exists. Try a different one.')
            conn.close()
            return redirect('/signup')

    return render_template('signup.html')

# ✅ LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['logged_in'] = True
            session['username'] = username
            flash(f'Welcome, {username}!')
            return redirect('/orders')
        else:
            flash('Invalid username or password.')
            return redirect('/login')

    return render_template('login.html')

# ✅ FORGOT PASSWORD
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        security_answer = request.form['security_answer']
        new_password = request.form['new_password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and user['security_answer'].lower() == security_answer.lower():
            new_password_hash = generate_password_hash(new_password)
            conn.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_hash, username))
            conn.commit()
            conn.close()
            flash('Password reset successful. You can now log in.')
            return redirect('/login')
        else:
            conn.close()
            flash('Invalid username or incorrect answer to security question.')
            return redirect('/forgot-password')

    return render_template('forgot_password.html')

# ✅ LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    session.pop('cart', None)
    flash('You have been logged out.')
    return redirect('/login')

# ✅ View All Orders (Admin)
@app.route('/orders')
def view_orders():
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

# ✅ Delete an Order
@app.route('/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db_connection()
    conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    flash('Order deleted successfully!')
    return redirect('/orders')

# ✅ Edit Order (Form)
@app.route('/edit/<int:order_id>', methods=['GET'])
def edit_order(order_id):
    if not session.get('logged_in'):
        return redirect('/login')
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    return render_template('edit_order.html', order=order)

# ✅ Update Order Logic
@app.route('/update/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if not session.get('logged_in'):
        return redirect('/login')
    item = request.form['item']
    qty = request.form['qty']

    conn = get_db_connection()
    conn.execute('UPDATE orders SET item = ?, qty = ? WHERE id = ?', (item, qty, order_id))
    conn.commit()
    conn.close()
    flash('Order updated successfully!')
    return redirect('/orders')

# ✅ Add to Cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    food_id = request.form['food_id']
    name = request.form['name']
    price = float(request.form['price'])

    cart = session.get('cart', {})

    if food_id in cart:
        cart[food_id]['quantity'] += 1
    else:
        cart[food_id] = {
            'name': name,
            'price': price,
            'quantity': 1
        }

    session['cart'] = cart
    flash(f"{name} added to cart!")
    return redirect('/menu')

# ✅ View Cart Page
@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)

# ✅ Update or Remove Items from Cart
@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', {})

    remove_id = request.form.get('remove')
    if remove_id:
        cart.pop(remove_id, None)
        session['cart'] = cart
        flash('Item removed from cart.')
        return redirect('/cart')

    for food_id in list(cart.keys()):
        qty_field = f'quantity_{food_id}'
        if qty_field in request.form:
            try:
                new_qty = int(request.form[qty_field])
                if new_qty > 0:
                    cart[food_id]['quantity'] = new_qty
            except ValueError:
                pass

    session['cart'] = cart
    flash('Cart updated successfully!')
    return redirect('/cart')

if __name__ == '__main__':
    app.run(debug=True)
