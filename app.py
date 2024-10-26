from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
def init_sqlite_db():
    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_name TEXT NOT NULL,
            bus_name TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            price REAL NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            seat_number TEXT NOT NULL,
            is_booked BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (route_id) REFERENCES routes (id)
        )''')
    conn.close()

init_sqlite_db()

@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to login page at server start

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        with sqlite3.connect('bus_ticket_booking.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Username already exists. Please choose a different one.', 'error')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hardcoded check for admin credentials
        if username == 'admin' and password == 'adminpass':
            session['user'] = 'admin'
            return redirect(url_for('admin_dashboard'))

        # Normal user login check
        with sqlite3.connect('bus_ticket_booking.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            record = cursor.fetchone()
        
        if record and check_password_hash(record[0], password):
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('main_page'))
        
        flash('Incorrect username or password. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/main')
def main_page():
    if 'user' not in session:
        flash('You must log in first!', 'error')
        return redirect(url_for('login'))
    return render_template('main.html', user=session['user'])

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    if 'user' not in session or session['user'] != 'admin':
        flash('Unauthorized access to admin dashboard!', 'error')
        return redirect(url_for('login'))
    
    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM routes")
        routes = cursor.fetchall()
    
    return render_template('admin.html', routes=routes)

@app.route('/view-route', methods=['GET'])
def view_route():
    if 'user' not in session or session['user'] != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('login'))

    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM routes")
        routes = cursor.fetchall()
    
    return render_template('view-route.html', routes=routes)

@app.route('/delete-route/<int:route_id>', methods=['POST'])
def delete_route(route_id):
    if 'user' not in session or session['user'] != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('login'))

    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM routes WHERE id = ?", (route_id,))
        conn.commit()
        
    flash('Route deleted successfully!', 'success')
    return redirect(url_for('view_route'))

@app.route('/add-route', methods=['GET', 'POST'])
def add_route():
    if 'user' not in session or session['user'] != 'admin':
        flash('Unauthorized access!', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        bus_name = request.form['bus_name']
        route_name = request.form['route_name']
        departure_time = request.form['departure_time']
        price = request.form['price']
        
        with sqlite3.connect('bus_ticket_booking.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO routes (route_name, bus_name, departure_time, price) VALUES (?, ?, ?, ?)",
                           (route_name, bus_name, departure_time, price))
            conn.commit()
        
        flash('Bus route added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add-route.html')  # Render the form for adding a route

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/book-bus')
def book_bus():
    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM routes")
        routes = cursor.fetchall()
    return render_template('book-bus.html', routes=routes)

@app.route('/book/<int:route_id>', methods=['GET', 'POST'])
def book(route_id):
    if 'user' not in session:
        flash('You must log in first!', 'error')
        return redirect(url_for('login'))
    
    with sqlite3.connect('bus_ticket_booking.db') as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            selected_seat = request.form['selected_seat']

            # Mark the seat as booked
            cursor.execute("UPDATE seats SET is_booked = 1 WHERE route_id = ? AND seat_number = ?",
                           (route_id, selected_seat))
            conn.commit()

            flash(f'Booking successful for seat {selected_seat} on route ID: {route_id}', 'success')
            return redirect(url_for('book_bus'))

        # Fetch available seats for the selected route
        cursor.execute("SELECT seat_number FROM seats WHERE route_id = ? AND is_booked = 0", (route_id,))
        available_seats = cursor.fetchall()

    return render_template('available-seats.html', route_id=route_id, available_seats=available_seats)

@app.errorhandler(404)
def not_found(e):
    return "This route does not exist", 404

if __name__ == '__main__':
    app.run(debug=True)
