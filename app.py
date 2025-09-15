from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas

from models import db, User, Appointment, Report

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # replace with any random string
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient_system.db'
db.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------ Routes ------------------

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "error")
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists", "error")
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now login.", "success")
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/appointment', methods=['GET','POST'])
@login_required
def appointment():
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        date = request.form['date']
        time = request.form['time']
        new_app = Appointment(patient_id=current_user.id, doctor_id=doctor_id, date=date, time=time)
        db.session.add(new_app)
        db.session.commit()
        flash("Appointment booked successfully!")
    return render_template('appointment.html')

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        report_details = request.form['report_details']
        
        new_report = Report(patient_name=patient_name, report_details=report_details)
        db.session.add(new_report)
        db.session.commit()
        flash("Report added successfully!", "success")
        return redirect(url_for('report'))

    reports = Report.query.all()
    return render_template('report.html', reports=reports)


@app.route('/report/<int:patient_id>')
@login_required
def generate_report(patient_id):
    if current_user.role != "doctor":
        flash("Only doctors can generate reports")
        return redirect(url_for('dashboard'))

    file_path = f"static/report_{patient_id}.pdf"
    c = canvas.Canvas(file_path)
    c.drawString(100, 750, f"Patient Report for ID: {patient_id}")
    c.drawString(100, 700, "Progress notes and details go here...")
    c.save()
    return f"Report generated: <a href='/{file_path}'>Download</a>"


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))


# ------------------ Run App ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
