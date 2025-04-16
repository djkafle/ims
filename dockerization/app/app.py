from flask import Flask, render_template, redirect, url_for, request, session, flash
import mysql.connector
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('MYSQL_HOST'),
        user=os.environ.get('MYSQL_USER'),
        password=os.environ.get('MYSQL_PASSWORD'),
        database=os.environ.get('MYSQL_DB')
    )

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Access denied: Admins only.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT user.*, roles.role 
            FROM user 
            LEFT JOIN roles ON user.role_id = roles.role_id 
            WHERE email = %s AND password = %s AND status = "enabled"
        ''', (email, password))
        account = cursor.fetchone()
        cursor.close()
        conn.close()
        if account:
            session['loggedin'] = True
            session['userid'] = account['userid']
            session['name'] = account['name']
            session['email'] = account['email']
            session['role'] = account['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials or disabled account')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT user.*, roles.role 
        FROM user 
        LEFT JOIN roles ON user.role_id = roles.role_id
    ''')
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('dashboard.html', users=users, role=session['role'])

@app.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM roles')
    roles = cursor.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role']
        status = request.form['status']
        department = request.form['department']
        country = request.form['country']
        cursor.execute('''
            INSERT INTO user (name, email, password, role_id, status, department, country) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (name, email, password, role_id, status, department, country))
        conn.commit()
        flash('User added successfully')
        return redirect(url_for('dashboard'))
    cursor.close()
    conn.close()
    return render_template('add_user.html', roles=roles)

@app.route('/update_user/<int:userid>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_user(userid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM roles')
    roles = cursor.fetchall()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role_id = request.form['role']
        status = request.form['status']
        department = request.form['department']
        country = request.form['country']
        cursor.execute('''
            UPDATE user 
            SET name=%s, email=%s, role_id=%s, status=%s, department=%s, country=%s 
            WHERE userid=%s
        ''', (name, email, role_id, status, department, country, userid))
        conn.commit()
        flash('User updated successfully')
        return redirect(url_for('dashboard'))
    cursor.execute('SELECT * FROM user WHERE userid = %s', (userid,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('update_user.html', user=user, roles=roles)

@app.route('/delete_user/<int:userid>', methods=['POST'])
@login_required
@admin_required
def delete_user(userid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT status FROM user WHERE userid = %s', (userid,))
    user = cursor.fetchone()
    if user and user['status'] == 'disabled':
        cursor.execute('DELETE FROM user WHERE userid = %s', (userid,))
        conn.commit()
        flash('User deleted successfully')
    else:
        flash('User must be disabled before deletion')
    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/roles')
@login_required
@admin_required
def manage_roles():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM roles')
    roles = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('roles.html', roles=roles)

@app.route('/add_role', methods=['GET', 'POST'])
@login_required
@admin_required
def add_role():
    if request.method == 'POST':
        role = request.form['role']
        description = request.form['description']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO roles (role, description) VALUES (%s, %s)', (role, description))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Role added successfully')
        return redirect(url_for('manage_roles'))
    return render_template('add_role.html')

@app.route('/edit_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_role(role_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        role = request.form['role']
        description = request.form['description']
        cursor.execute('UPDATE roles SET role = %s, description = %s WHERE role_id = %s', (role, description, role_id))
        conn.commit()
        flash('Role updated successfully')
        return redirect(url_for('manage_roles'))
    cursor.execute('SELECT * FROM roles WHERE role_id = %s', (role_id,))
    role = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_role.html', role=role)

@app.route('/delete_role/<int:role_id>', methods=['POST'])
@login_required
@admin_required
def delete_role(role_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM roles WHERE role_id = %s', (role_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Role deleted successfully')
    return redirect(url_for('manage_roles'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
