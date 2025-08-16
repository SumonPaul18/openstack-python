from flask import Flask, redirect, url_for, flash, render_template, request
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)
from main import app, db
#from models import User

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



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Add registration logic here
        pass
    return render_template('register.html')

@app.route('/notification')
@login_required
def notification():
    return render_template('notification.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

