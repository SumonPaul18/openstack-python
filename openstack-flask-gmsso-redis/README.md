# Flask Web Application with Dashboard, Google/Email Auth, and Redis Session Management

This project is a full-stack web application built using the Flask framework. The main objective is to create a robust and secure authentication system that supports both traditional email/password registration and modern social login via Google. The application features a dynamic dashboard accessible only to authenticated users, with a scalable session management system powered by Redis for a seamless user experience.

The long-term plan is to expand this project into a microservices architecture, where the authentication service (this project) can be integrated with other services for a complete Single Sign-On (SSO) solution. The primary goal is to provide a highly scalable, secure, and user-friendly authentication foundation for future projects.

-----

## 🌟 Features

  * **User Authentication**:
      * **Google Sign-in**: Fast and secure login using Google's OAuth 2.0.
      * **Email/Password Login**: Traditional registration and authentication with email verification.
      * **Password Reset**: Secure password recovery functionality.
  * **Session Management**: Scalable and distributed session handling using **Redis** and **Flask-Session**.
  * **Secure Dashboard**: A protected area accessible only to logged-in users.
  * **Database**: **SQLite** via **Flask-SQLAlchemy** for storing user and OAuth data.
  * **Configuration**: Sensitive information is managed securely using environment variables from a `.env` file.

-----

## 🛠️ Technology Stack

  * **Backend**: Python, Flask
  * **Database**: SQLite (managed by Flask-SQLAlchemy)
  * **Session Store**: Redis
  * **Authentication**: Flask-Login, Flask-Dance (Google OAuth)
  * **Email Service**: Flask-Mail

-----

## 🚀 Setup Guide

Follow these steps to set up and run the project on your local machine.

### Prerequisites

  * Python 3.8+
  * pip (Python package installer)
  * A running Redis server (e.g., at IP address `192.168.0.207` on port `6379`).

### Installation

1.  **Clone the repository**:

    ```bash
    git clone <YOUR-REPOSITORY-URL>
    cd openstack-python-flask-gmsso-redis
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    Install all required Python packages from the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file in the project's root directory and fill in your information based on the example below.

    ```env
    SECRET_KEY="your_flask_secret_key_here"
    GOOGLE_CLIENT_ID="your_google_client_id"
    GOOGLE_CLIENT_SECRET="your_google_client_secret"
    MAIL_SERVER="smtp.gmail.com"
    MAIL_PORT=587
    MAIL_USERNAME="your_email@gmail.com"
    MAIL_PASSWORD="your_email_app_password"
    ```

    **Note**: It is highly recommended to use a [Google App Password](https://support.google.com/accounts/answer/185833?hl=bn) for `MAIL_PASSWORD` instead of your regular email password.

5.  **Set up the database**:
    Run the following command to create the database tables. This will create a `signup-update8.db` file.

    ```bash
    python app.py --setup
    ```

6.  **Run the application**:
    Now you can run the application.

    ```bash
    python app.py
    ```

    The application will be running at `http://0.0.0.0:5000`. You can access it from your web browser at `http://127.0.0.1:5000` or your machine's IP address (`http://192.168.0.93:5000`).

-----

## 📝 Usage

### For Developers

  * **Access the Dashboard**: Once authenticated, you will be redirected to the secure dashboard.
  * **Run a Development Server**: The application is configured to run in debug mode, which automatically reloads the server on code changes.
  * **Database Management**: The SQLite database simplifies development, but you can easily switch to a more robust database like PostgreSQL or MySQL for a production environment.

### For Users

  * **Sign Up**: Create an account using your email and a strong password. You will receive a confirmation email to activate your account.
  * **Log In**: Use your registered credentials or the Google Sign-in button to access your dashboard.
  * **Forgot Password**: Follow the password reset link on the login page to securely reset your password via email.
  * **Dashboard**: After logging in, you can access your personalized dashboard.

-----

## 🤝 Contributing

We welcome contributions\! If you would like to contribute, please feel free to submit a pull request or open an issue.

-----

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

-----

## ✉️ Contact

For any questions or support, please feel free to reach out to [Your Name/Email/GitHub Profile Link].
