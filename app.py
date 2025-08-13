from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management
init_db()

@app.route('/')
def main():
    return redirect(url_for('login'))

@app.route('/add-medication', methods=['GET', 'POST'])
def add_medication():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        med_name = request.form.get('medication_name', '').strip()
        dosage = request.form.get('dosage', '').strip()
        timing = request.form.getlist('timing')
        userID = session.get('userID')
        if not med_name or not dosage or not timing:
            flash('Please fill all fields.')
            return redirect(url_for('add_medication'))
        conn = get_db_connection()
        conn.execute('INSERT INTO medications (userID, MedicationName, DosageAmount, Frequency) VALUES (?, ?, ?, ?)',
                     (userID, med_name, dosage, ', '.join(timing)))
        conn.commit()
        conn.close()
        flash('Medication added!')
        return redirect(url_for('add_medication'))
    return render_template('add_medication.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Please enter both username and password.')
            return redirect(url_for('login'))
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE Username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['Password'], password):
            session['username'] = username
            session['userID'] = user['userID']
            session['role'] = user['Role']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('userID', None)
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = 'User'
        if not email or not username or not password:
            flash('Please fill all fields.')
            return redirect(url_for('register'))
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE Username = ?', (username,)).fetchone()
        existing_email = conn.execute('SELECT * FROM users WHERE Email = ?', (email,)).fetchone()
        if existing_user:
            flash('Username already exists.')
            conn.close()
            return redirect(url_for('register'))
        if existing_email:
            flash('Email already exists.')
            conn.close()
            return redirect(url_for('register'))
        userID = str(uuid.uuid4())[:6]
        hashed_pw = generate_password_hash(password)
        conn.execute('INSERT INTO users (userID, Username, Password, Email, Role) VALUES (?, ?, ?, ?, ?)',
                     (userID, username, hashed_pw, email, role))
        conn.commit()
        conn.close()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Save reminder preferences to DB (not implemented)
        flash('Reminder preferences saved!')
        return redirect(url_for('reminders'))
    return render_template('reminders.html')

@app.route('/caregiver')
def caregiver():
    if 'username' not in session:
        return redirect(url_for('login'))
    # Fetch medication history for caregiver (not implemented)
    return render_template('caregiver.html')

@app.route('/medication-logging', methods=['GET', 'POST'])
def medication_logging():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    userID = session.get('userID')
    meds = conn.execute('SELECT * FROM medications WHERE userID = ?', (userID,)).fetchall()
    if request.method == 'POST':
        med_id = request.form.get('medication')
        status = request.form.get('status')
        notes = request.form.get('notes', '').strip()
        conn.execute('''CREATE TABLE IF NOT EXISTS medication_logs (
            logID INTEGER PRIMARY KEY AUTOINCREMENT,
            userID TEXT,
            medicationID INTEGER,
            status TEXT,
            notes TEXT,
            logTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(userID) REFERENCES users(userID),
            FOREIGN KEY(medicationID) REFERENCES medications(medicationID)
        )''')
        conn.execute('INSERT INTO medication_logs (userID, medicationID, status, notes) VALUES (?, ?, ?, ?)',
                     (userID, med_id, status, notes))
        conn.commit()
        flash('Medication log saved!')
        return redirect(url_for('medication_logging'))
    conn.close()
    return render_template('medication_logging.html', meds=meds)

@app.route('/health-report')
def health_report():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    userID = session.get('userID')
    missed_logs = conn.execute('SELECT * FROM medication_logs WHERE userID = ? AND status = "Missed"', (userID,)).fetchall()
    total_logs = conn.execute('SELECT * FROM medication_logs WHERE userID = ?', (userID,)).fetchall()
    conn.close()
    missed_count = len(missed_logs)
    total_count = len(total_logs)
    return render_template('health_report.html', missed_count=missed_count, total_count=total_count, missed_logs=missed_logs)

@app.route('/admin')
def admin_panel():
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/admin/toggle/<user_id>', methods=['POST'])
def admin_toggle(user_id):
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE userID = ?', (user_id,)).fetchone()
    new_status = 0 if user['reminderStatus'] else 1
    conn.execute('UPDATE users SET reminderStatus = ? WHERE userID = ?', (new_status, user_id))
    conn.commit()
    conn.close()
    flash('User status updated.')
    return redirect(url_for('admin_panel'))

@app.route('/admin/reset/<user_id>', methods=['POST'])
def admin_reset_password(user_id):
    if 'username' not in session or session.get('role') != 'Admin':
        return redirect(url_for('login'))
    # For demo, reset password to 'password123'
    from werkzeug.security import generate_password_hash
    new_pw = generate_password_hash('password123')
    conn = get_db_connection()
    conn.execute('UPDATE users SET Password = ? WHERE userID = ?', (new_pw, user_id))
    conn.commit()
    conn.close()
    flash('Password reset to "password123".')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000)
