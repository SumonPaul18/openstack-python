# main.py

import sys
import os
import re
from flask import Flask, redirect, url_for, flash, render_template, request, session, jsonify
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

# --- Authlib imports for Keycloak ---
from authlib.integrations.flask_client import OAuth as AuthlibOAuth
from authlib.common.security import generate_token
import requests # For fetching Keycloak configuration if needed
# ------------------------------------

# Load environment variables from .env file
load_dotenv()

# setup Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# setup Redis session
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://192.168.0.207:6379') # Update Redis URL if needed
Session(app)

# setup database models
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///signup-update8.db"
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=True) # username nullable করা হয়েছে
    email = db.Column(db.String(256), unique=True)
    name = db.Column(db.String(256), nullable=True) # name nullable করা হয়েছে
    profile_pic = db.Column(db.String(256), nullable=True) # profile_pic nullable করা হয়েছে
    password_hash = db.Column(db.String(128), nullable=True) # password_hash nullable করা হয়েছে
    confirmed = db.Column(db.Boolean, default=False) # Email confirmation status
    reset_token = db.Column(db.String(128), nullable=True) # Password reset token

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OAuth(OAuthConsumerMixin, db.Model): # Rename to avoid conflict, or use a different name
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref=db.backref("oauth", cascade="all, delete-orphan"))

# setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # Redirect to 'login' if not authenticated

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# setup Google OAuth (বিদ্যমান)
google_blueprint = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email", "openid"], # Added 'openid' scope
    redirect_to="index"
)
google_blueprint.backend = SQLAlchemyStorage(OAuth, db.session, user=current_user)
app.register_blueprint(google_blueprint, url_prefix="/login")


# --- Keycloak Setup using Authlib ---
oauth = AuthlibOAuth(app) # Create an OAuth instance for Authlib

# Register Keycloak as an OAuth provider
keycloak = oauth.register(
    name='keycloak',
    client_id=os.getenv("KEYCLOAK_CLIENT_ID"),
    client_secret=os.getenv("KEYCLOAK_CLIENT_SECRET"),
    server_metadata_url=f'{os.getenv("KEYCLOAK_SERVER_URL")}/realms/{os.getenv("KEYCLOAK_REALM")}/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile', # Define required scopes
    },
)
# ------------------------------------

# setup Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
mail = Mail(app)

# --- Keycloak Login Route ---
@app.route('/login/keycloak')
def login_keycloak():
    redirect_uri = url_for('auth_keycloak', _external=True)
    return keycloak.authorize_redirect(redirect_uri)

@app.route('/auth/keycloak')
def auth_keycloak():
    try:
        # Get the authorization token from Keycloak
        token = keycloak.authorize_access_token()
        user_info = token.get('userinfo') # Get user info directly from token if available

        if not user_info:
            # If userinfo is not in token, fetch it explicitly
            user_info_response = keycloak.get('userinfo')
            user_info = user_info_response.json()

        if user_info:
            # Extract user details from Keycloak response
            keycloak_user_id = user_info.get('sub') # Unique ID from Keycloak
            user_email = user_info.get('email')
            user_name = user_info.get('name') or user_info.get('preferred_username')

            if not user_email:
                flash("Could not retrieve email from Keycloak.", "danger")
                return redirect(url_for('login'))

            # Check if user already exists in local database
            existing_user = User.query.filter_by(email=user_email).first()

            if existing_user:
                # Link to existing user if not already linked
                oauth_entry = OAuth.query.filter_by(provider='keycloak', provider_user_id=keycloak_user_id).first()
                if not oauth_entry:
                    new_oauth = OAuth(
                        provider='keycloak',
                        provider_user_id=keycloak_user_id,
                        user_id=existing_user.id,
                        token=token # Store token if needed later
                    )
                    db.session.add(new_oauth)
                    db.session.commit()
                login_user(existing_user)
                flash("Successfully signed in with Keycloak.", "success")
                # Store user info in session for SSO-like behavior (optional, Flask-Login handles this)
                session['user_id'] = existing_user.id
                session['username'] = existing_user.username if existing_user.username else existing_user.email
                session['email'] = existing_user.email
            else:
                # Create a new user
                new_user = User(
                    email=user_email,
                    name=user_name,
                    username=user_email.split('@')[0], # Generate username from email
                    confirmed=True # Assume email is confirmed via Keycloak
                )
                db.session.add(new_user)
                db.session.flush() # Get the new user ID

                # Create OAuth link
                new_oauth = OAuth(
                    provider='keycloak',
                    provider_user_id=keycloak_user_id,
                    user_id=new_user.id,
                    token=token
                )
                db.session.add(new_oauth)
                db.session.commit()

                login_user(new_user)
                flash("Successfully registered and signed in with Keycloak.", "success")
                session['user_id'] = new_user.id
                session['username'] = new_user.username
                session['email'] = new_user.email

            return redirect(url_for('dashboard'))
        else:
            flash("Failed to retrieve user information from Keycloak.", "danger")
            return redirect(url_for('login'))

    except Exception as e:
        print(f"Keycloak OAuth error: {e}") # Log the error for debugging
        flash(f"OAuth error occurred: {str(e)}", "danger")
        return redirect(url_for('login'))
# ------------------------------------

# --- Keycloak Logout Route ---
@app.route('/logout/keycloak')
@login_required
def logout_keycloak():
    # Perform local logout first
    logout_user()
    session.clear()

    # Redirect to Keycloak logout endpoint (optional, for global logout)
    # Requires Keycloak session management to be configured properly
    keycloak_logout_url = f"{os.getenv('KEYCLOAK_SERVER_URL')}/realms/{os.getenv('KEYCLOAK_REALM')}/protocol/openid-connect/logout"
    # You might need to pass the ID token or refresh token depending on Keycloak config
    # For simplicity, just redirecting to Keycloak logout page without token revocation here.
    # A more robust implementation would retrieve the ID token from the session/token and pass it.
    # Example (basic redirect, might require post-logout redirect URI setup in Keycloak client):
    post_logout_redirect_uri = url_for('index', _external=True) # Or your desired post-logout page
    logout_url_with_redirect = f"{keycloak_logout_url}?redirect_uri={post_logout_redirect_uri}"
    flash("You have been logged out from the application and Keycloak.", "info")
    return redirect(logout_url_with_redirect)
    # return redirect(url_for('index')) # Simpler local logout only

# ------------------------------------


# Existing Google OAuth logic (simplified, check original for full logic)
@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    # ... (Your existing Google login logic) ...
    # Make sure to return False at the end to prevent flask-dance from doing its default login
    # if you are handling login yourself as shown in the original code.
    # return False # Important if you handle login manually
    pass # Placeholder, replace with your actual logic

@oauth_error.connect_via(google_blueprint)
def google_error(blueprint, error, error_description=None, error_uri=None):
    # ... (Your existing Google error logic) ...
    pass # Placeholder

# ... (Rest of your existing routes and functions like index, login, signup, reset_password, etc.) ...

# Example route to show Keycloak login button
@app.route('/login')
def login():
    # You can modify your existing login template to include the Keycloak button
    # pointing to url_for('login_keycloak')
    return render_template('login.html') # Ensure your login.html includes the Keycloak link/button

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html') # Or your desired dashboard template

@app.route('/')
def index():
    return render_template('home.html') # Or your desired index template

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) # Adjust host/port as needed