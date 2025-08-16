import sys
import os
import re
from flask import Flask, redirect, url_for, flash, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from flask_session import Session # Import Flask-Session
import redis # Import redis library

# Load environment variables from .env file
load_dotenv()

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# setup Flask application
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersekrit")

# Configure Flask-Session to use Redis
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
# Redis সার্ভারের IP অ্যাড্রেস এবং পোর্ট এখানে দিন
app.config["SESSION_REDIS"] = redis.StrictRedis(host='192.168.0.207', port=6379, db=0)

server_session = Session(app) # Initialize Flask-Session

# setup database models
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///signup-update8.db"
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=True) # username nullable করা হয়েছে
    email = db.Column(db.String(256), unique=True)
    name = db.Column(db.String(256), nullable=True) # name nullable করা হয়েছে
    profile_pic = db.Column(db.String(256), nullable=True) # profile_pic nullable করা হয়েছে
    password = db.Column(db.String(256), nullable=True) # password nullable করা হয়েছে
    confirmed = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(256), nullable=True)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

# setup login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# setup Google OAuth
blueprint = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email", "openid"], # Added 'openid' scope
    redirect_to="index"
)
blueprint.backend = SQLAlchemyStorage(OAuth, db.session, user=current_user)
app.register_blueprint(blueprint, url_prefix="/login")

# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Google.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", category="error")
        return False

    google_info = resp.json()
    if not google_info:
        flash("No user info returned from Google.", category="error")
        return False

    google_user_id = google_info.get("id")
    if not google_user_id:
        flash("No user ID returned from Google.", category="error")
        return False

    query = OAuth.query.filter_by(
        provider=blueprint.name,
        provider_user_id=google_user_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider=blueprint.name,
            provider_user_id=google_user_id,
            token=token,
        )

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with Google.")
        # Store user info in session for SSO-like behavior
        session['user_id'] = oauth.user.id
        session['username'] = oauth.user.username if oauth.user.username else oauth.user.email
        session['email'] = oauth.user.email
        return redirect(url_for("dashboard"))
    else:
        user_email = google_info.get("email")
        # Check if a user with this email already exists from manual signup
        existing_user = User.query.filter_by(email=user_email).first()

        if existing_user:
            # Link existing user to OAuth
            oauth.user = existing_user
            db.session.add(oauth)
            db.session.commit()
            login_user(existing_user)
            flash("Successfully linked existing account and signed in with Google.")
            session['user_id'] = existing_user.id
            session['username'] = existing_user.username if existing_user.username else existing_user.email
            session['email'] = existing_user.email
            return redirect(url_for("dashboard"))
        else:
            # Create new user and link to OAuth
            user = User(
                email=google_info.get("email"),
                name=google_info.get("name"),
                profile_pic=google_info.get("picture"),
                # For Google Sign-in, username can be the email if no specific username is provided
                username=google_info.get("email"),
                confirmed=True # Google users are considered confirmed
            )
            oauth.user = user
            db.session.add_all([user, oauth])
            db.session.commit()
            login_user(user)
            flash("Successfully signed in with Google.")
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            return redirect(url_for("dashboard"))

    print(f"Logged in user: {current_user.name}, {current_user.email}")
    return False

# notify on OAuth provider error
@oauth_error.connect_via(blueprint)
def google_error(blueprint, error, error_description=None, error_uri=None):
    msg = (
        "OAuth error from {name}! "
        "error={error} description={description} uri={uri}"
    ).format(
        name=blueprint.name,
        error=error,
        description=error_description,
        uri=error_uri,
    )
    flash(msg, category="error")

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=app.config['MAIL_USERNAME']
    )
    mail.send(msg)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt=app.secret_key)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        email = serializer.loads(
            token,
            salt=app.secret_key,
            max_age=expiration
        )
    except SignatureExpired:
        return False
    return email

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear() # Clear the session data
    flash("You have logged out", "info")
    return redirect(url_for('login'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard")) # Redirect to dashboard if already logged in
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))
        
        # Validate password strength (example - customize as needed)
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            flash("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.", "danger")
            return redirect(url_for("signup"))

        hashed_password = generate_password_hash(password, method='sha256')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email address already exists. Please login instead.", "warning")
            return redirect(url_for("login"))

        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            confirmed=False
        )
        db.session.add(new_user)
        db.session.commit()

        token = generate_confirmation_token(new_user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        try:
            send_email(new_user.email, 'Confirm Your Account', html)
            flash("A confirmation email has been sent to your email address. Please check your inbox (and spam folder) to activate your account.", "info")
        except Exception as e:
            db.session.delete(new_user)
            db.session.commit()
            flash(f"Error sending confirmation email: {e}. Please try again later.", "danger")
            return redirect(url_for("signup"))
            
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except SignatureExpired:
        flash('The confirmation link has expired.', 'danger')
        return redirect(url_for('signup'))
    
    user = User.query.filter_by(email=email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        db.session.commit()
        login_user(user)
        flash('You have successfully confirmed your account!', 'success')
    return redirect(url_for('dashboard'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard")) # Redirect to dashboard if already logged in

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.confirmed:
                flash('Please confirm your account before logging in.', 'warning')
                return redirect(url_for('login'))
            login_user(user)
            flash("Logged in successfully!")
            # Store user info in session for SSO-like behavior
            session['user_id'] = user.id
            session['username'] = user.username if user.username else user.email
            session['email'] = user.email
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html")

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("No account found with that email address.", "danger")
            return redirect(url_for("reset_password"))
        
        token = generate_confirmation_token(user.email)
        user.reset_token = token
        db.session.commit()

        reset_url = url_for('reset_password_token', token=token, _external=True)
        html = render_template('reset_password_email.html', reset_url=reset_url)
        try:
            send_email(user.email, 'Password Reset Request', html)
            flash("A password reset email has been sent to your email address. Please check your inbox (and spam folder).", "info")
        except Exception as e:
            flash(f"Error sending password reset email: {e}. Please try again later.", "danger")
        return redirect(url_for("login"))
    return render_template("reset_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password_token(token):
    try:
        email = confirm_token(token)
    except SignatureExpired:
        flash("The reset link has expired.", "danger")
        return redirect(url_for("reset_password"))

    user = User.query.filter_by(email=email).first_or_404()
    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            flash("Passwords do not match!", "danger") # Changed to danger for consistency
            return redirect(url_for("reset_password_token", token=token))

        # Validate password strength (example - customize as needed)
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            flash("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.", "danger")
            return redirect(url_for("reset_password_token", token=token))

        hashed_password = generate_password_hash(password, method='sha256')
        user.password = hashed_password
        user.reset_token = None
        db.session.commit()
        flash("Your password has been updated!", "success") # Changed to success for consistency
        return redirect(url_for("login"))

    return render_template("reset_password_token.html", token=token)

@app.route("/")
def index():
    # Check if user is logged in via Flask-Login and session data exists
    if current_user.is_authenticated and 'user_id' in session:
        # User is logged in, redirect to dashboard
        return redirect(url_for("dashboard"))
    else:
        # User is not logged in, render home page
        return render_template("home.html")
