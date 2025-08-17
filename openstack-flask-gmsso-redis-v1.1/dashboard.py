# dashboard.py
from flask import render_template
from flask_login import login_required
from main import app

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('sidebar3.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/task')
@login_required
def task():
    return render_template('task.html')

@app.route('/notification')
@login_required
def notification():
    return render_template('notification.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')