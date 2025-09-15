from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ Models ------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), default='patient')  # roles: patient, doctor

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    report_details = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.String(50), default=datetime.now().strftime("%Y-%m-%d %H:%M"))

# ------------------ Login Manager ------------------
login_manager = LoginManager()
login_manager.login_view = 'login'
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
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
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
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now login.", "success")
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    return render_template('dashboard.html', appointments=appointments)

@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    if request.method == 'POST':
        patient_name = current_user.username
        doctor_name = request.form['doctor']
        date = request.form['date']
        time = request.form['time']
        new_app = Appointment(patient_id=current_user.id, doctor_name=doctor_name, date=date, time=time)
        db.session.add(new_app)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('appointment'))
    appointments = Appointment.query.filter_by(patient_id=current_user.id).all()
    return render_template('appointment.html', appointments=appointments)

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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

# ------------------ Run App ------------------
if __name__ == '__main__':
    if not os.path.exists('patient_system.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
