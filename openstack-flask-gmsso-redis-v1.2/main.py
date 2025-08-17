# main.py
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
from flask_session import Session
import redis
import openstack

# Load environment variables
load_dotenv()

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Flask App Setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersekrit")

# Redis Session Configuration
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "192.168.0.207"),
    port=6379,
    db=0,
    decode_responses=False
)
server_session = Session(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///signup-update8.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=True)
    email = db.Column(db.String(256), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=True)
    profile_pic = db.Column(db.String(256), nullable=True)
    password = db.Column(db.String(256), nullable=True)
    confirmed = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(256), nullable=True)

    # OpenStack Integration
    openstack_user_id = db.Column(db.String(128), nullable=True)
    openstack_project_id = db.Column(db.String(128), nullable=True)
    openstack_network_id = db.Column(db.String(128), nullable=True)
    openstack_subnet_id = db.Column(db.String(128), nullable=True)
    openstack_router_id = db.Column(db.String(128), nullable=True)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User, backref=db.backref("oauth", cascade="all, delete-orphan"))

# Login Manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Password strength checker
def is_password_strong(password):
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@$!%*?&]", password):
        return False
    return True

# Google OAuth Blueprint
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_url="/google-login"
)
google_bp.storage = SQLAlchemyStorage(OAuth, db.session, user=lambda: current_user)
app.register_blueprint(google_bp, url_prefix="/login")

# Create OpenStack User, Project, Network, Subnet, Router
def create_openstack_resources(user):
    if user.openstack_project_id and user.openstack_user_id:
        return  # Already created

    try:
        # Connect as admin using clouds.yaml
        conn = openstack.connect(cloud='openstack')

        # === 1. Create Project ===
        project_name = f"project_{user.id}"
        project = conn.identity.create_project(
            name=project_name,
            description=f"Project for {user.email}",
            domain="default"
        )

        # === 2. Create User ===
        os_user = conn.identity.create_user(
            name=user.email,
            email=user.email,
            password=os.urandom(12).hex(),
            domain="default"
        )

        # Set as default project
        conn.identity.update_user(os_user.id, default_project_id=project.id)

        # === 3. Assign Roles ===
        member_role = conn.identity.find_role("member")
        if not member_role:
            member_role = conn.identity.create_role(name="member")

        admin_role = conn.identity.find_role("admin")

        conn.identity.assign_project_role_to_user(project.id, os_user.id, member_role.id)

        # Add default admin as admin of this project
        admin_user = conn.identity.find_user("admin", domain_id="default")
        if admin_user and admin_role:
            conn.identity.assign_project_role_to_user(project.id, admin_user.id, admin_role.id)

        # === 4. Create Network ===
        network_name = f"{project_name}-private"
        network = conn.network.create_network(
            name=network_name,
            project_id=project.id
        )
        print(f"✅ Network created: {network_name}")

        # === 5. Create Subnet ===
        subnet_name = f"{project_name}-subnet"
        subnet = conn.network.create_subnet(
            name=subnet_name,
            network_id=network.id,
            ip_version=4,
            cidr="10.0.0.0/24",
            gateway_ip="10.0.0.1",
            project_id=project.id
        )
        print(f"✅ Subnet created: {subnet_name}")

        # === 6. Create Router & Attach External Gateway ===
        router_name = f"{project_name}-router"

        # 🔍 Find 'public' network by name
        public_network = conn.network.find_network("public")
        if not public_network:
            raise Exception("External network 'public' not found in OpenStack")

        router = conn.network.create_router(
            name=router_name,
            external_gateway_info={"network_id": public_network.id},  # ✅ Use ID
            project_id=project.id
        )
        print(f"✅ Router created: {router_name}")

        # === 7. Add Router Interface ===
        conn.network.add_interface_to_router(
            router, subnet_id=subnet.id
        )
        print(f"✅ Interface added to router: {subnet_name}")

        # === 8. Save IDs in database ===
        user.openstack_user_id = os_user.id
        user.openstack_project_id = project.id
        user.openstack_network_id = network.id
        user.openstack_subnet_id = subnet.id
        user.openstack_router_id = router.id
        db.session.commit()

        print(f"✅ OpenStack setup complete for {user.email}")

    except Exception as e:
        db.session.rollback()
        print(f"❌ OpenStack setup failed: {e}")
        raise e

# Google Login Handler
@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Google.", "danger")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return False

    google_info = resp.json()
    email = google_info["email"]
    google_id = google_info["id"]

    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=google_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = None

    if oauth and oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with Google.", "success")
        return redirect(url_for("dashboard"))

    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            email=email,
            name=google_info.get("name"),
            profile_pic=google_info.get("picture"),
            username=email.split("@")[0],
            confirmed=True
        )
        db.session.add(user)
        db.session.flush()

        # Create OpenStack resources
        try:
            create_openstack_resources(user)
        except Exception as e:
            db.session.rollback()
            flash(f"Cloud setup failed: {str(e)}", "danger")
            return redirect(url_for("login"))

    if not oauth:
        oauth = OAuth(provider=blueprint.name, provider_user_id=google_id, token=token, user=user)
        db.session.add(oauth)
    else:
        oauth.user = user

    db.session.commit()
    login_user(user)
    flash("Welcome! Your cloud environment is ready.", "success")
    return redirect(url_for("dashboard"))

# OAuth Error Handler
@oauth_error.connect_via(google_bp)
def google_error(blueprint, error, error_description=None, error_uri=None):
    flash(f"OAuth error: {error} - {error_description}", "danger")

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template, sender=app.config['MAIL_USERNAME'])
    mail.send(msg)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps(email, salt=app.secret_key)

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        email = serializer.loads(token, salt=app.secret_key, max_age=expiration)
        return email
    except SignatureExpired:
        return False

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for('login'))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("signup"))

        if not is_password_strong(password.strip()):
            flash("Password must meet the required criteria.", "danger")
            return redirect(url_for("signup"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(url_for("login"))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            confirmed=False
        )
        db.session.add(user)
        db.session.flush()

        try:
            create_openstack_resources(user)
            token = generate_confirmation_token(user.email)
            confirm_url = url_for('confirm_email', token=token, _external=True)
            html = render_template('activate.html', confirm_url=confirm_url)
            send_email(user.email, 'Confirm Your Account', html)
            flash("A confirmation email has been sent.", "info")
        except Exception as e:
            db.session.delete(user)
            db.session.commit()
            flash(f"Cloud setup failed: {str(e)}", "danger")
            return redirect(url_for("signup"))

        db.session.commit()
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash('The confirmation link has expired.', 'danger')
        return redirect(url_for('signup'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('signup'))

    if user.confirmed:
        flash('Account already confirmed.', 'success')
    else:
        user.confirmed = True
        db.session.commit()
        login_user(user)
        flash('Your account has been confirmed!', 'success')
    return redirect(url_for('dashboard'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.password and check_password_hash(user.password, password):
            if not user.confirmed:
                flash('Please confirm your account first.', 'warning')
                return redirect(url_for('login'))
            login_user(user)
            flash("Logged in successfully!", "success")
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
            flash("No account found with that email.", "danger")
            return redirect(url_for("reset_password"))

        token = generate_confirmation_token(user.email)
        user.reset_token = token
        db.session.commit()

        reset_url = url_for('reset_password_token', token=token, _external=True)
        html = render_template('reset_password_email.html', reset_url=reset_url)
        try:
            send_email(user.email, 'Password Reset Request', html)
            flash("Password reset link sent to your email.", "info")
        except Exception as e:
            flash(f"Failed to send email: {e}", "danger")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password_token(token):
    email = confirm_token(token)
    if not email:
        flash("The reset link has expired.", "danger")
        return redirect(url_for("reset_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("reset_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("reset_password_token", token=token))

        if not is_password_strong(password.strip()):
            flash("Password must meet the required criteria.", "danger")
            return redirect(url_for("reset_password_token", token=token))

        user.password = generate_password_hash(password)
        user.reset_token = None
        db.session.commit()
        flash("Your password has been updated!", "success")
        return redirect(url_for("login"))

    return render_template("reset_password_token.html", token=token)

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("home.html")