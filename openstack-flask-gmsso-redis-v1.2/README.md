# OpenStack Flask Web App with Google SSO & Redis Session Management

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)
![OpenStack](https://img.shields.io/badge/OpenStack-%E2%9C%93-orange)
![Redis](https://img.shields.io/badge/Redis-%E2%9C%93-purple)
![License](https://img.shields.io/github/license/SumonPaul18/openstack-python)

A secure, scalable **Flask-based web application** that integrates **OpenStack APIs**, **Google Single Sign-On (SSO)** authentication, and **Redis-backed session storage** for persistent, high-performance user management.

This project enables users to securely log in via Google OAuth 2.0, manage OpenStack cloud resources (e.g., instances, networks, images), and maintain authenticated sessions using Redis — ideal for production-grade deployments requiring centralized authentication and session persistence.

---

## 🌟 Features

✅ **Google SSO Authentication**  
Secure login using Google OAuth 2.0 with proper token validation.

✅ **OpenStack SDK Integration**  
Interact with OpenStack services (Nova, Neutron, Glance, etc.) via `python-openstacksdk`.

✅ **Redis Session Backend**  
Persistent, fast session storage using Redis — perfect for scaling across multiple instances.

✅ **Flask-Based Web Interface**  
Clean, modular Flask app with routes for login, dashboard, and resource management.

✅ **Environment-Driven Configuration**  
Secure configuration via `.env` files and environment variables.

✅ **Production-Ready Structure**  
Modular design suitable for deployment with Gunicorn, Nginx, Docker, or Kubernetes.

---

## 📦 Project Structure

```
openstack-flask-gmsso-redis-v1.2/
│
├── app/                       # Main Flask application
│   ├── __init__.py            # Flask app factory
│   ├── routes.py              # Web routes (login, dashboard, logout)
│   ├── auth.py                # Google OAuth 2.0 logic
│   ├── openstack_client.py    # OpenStack SDK integration
│   └── utils.py               # Helper functions
│
├── config/                    # Configuration files
│   ├── settings.py            # App settings & OAuth keys
│   └── .env.example           # Template for environment variables
│
├── static/                    # CSS, JS, images
│   └── style.css
│
├── templates/                 # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   └── base.html
│
├── requirements.txt           # Python dependencies
├── run.py                     # Entry point
├── docker-compose.yml         # Optional: Redis + App orchestration
└── README.md                  # This file
```

---

## 🔐 Google SSO Setup

To enable Google OAuth 2.0:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one.
3. Navigate to **APIs & Services > Credentials**.
4. Click **Create Credentials > OAuth Client ID**.
5. Application type: **Web Application**
6. Add authorized redirect URIs:
   ```
   http://localhost:5000/login/callback
   ```
7. Copy the **Client ID** and **Client Secret** into your `.env` file.

> 🔐 Never commit your credentials. Use `.env` and keep it out of version control.

---

## ⚙️ Configuration

1. Copy the example environment file:
   ```bash
   cp config/.env.example config/.env
   ```

2. Edit `config/.env` with your actual values:

   ```env
   FLASK_APP=run.py
   FLASK_ENV=development

   # Google OAuth 2.0
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_DISCOVERY_URL=https://accounts.google.com/.well-known/openid-configuration

   # OpenStack Credentials
   OS_AUTH_URL=https://your-openstack-auth-url:5000/v3
   OS_USERNAME=your-openstack-username
   OS_PASSWORD=your-openstack-password
   OS_PROJECT_NAME=your-project-name
   OS_USER_DOMAIN_NAME=Default
   OS_PROJECT_DOMAIN_NAME=Default

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # Session
   SECRET_KEY=your-super-secret-flask-key-here
   ```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Redis Server (or Docker)
- OpenStack account with API access
- Google Cloud Platform project with OAuth enabled

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/SumonPaul18/openstack-python.git
   cd openstack-python
   git checkout paulcolab/openstack-flask-gmsso-redis-v1.2
   ```

2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start Redis (via Docker or system service):
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

5. Run the Flask app:
   ```bash
   python run.py
   ```

6. Open in browser:
   ```
   http://localhost:5000
   ```

---

## 🖥️ Usage

- **Login Page**: Users are redirected to Google for authentication.
- **Dashboard**: After successful login, users see their Google profile and can interact with OpenStack resources.
- **Session Management**: Sessions are stored in Redis and encrypted using Flask’s `SECRET_KEY`.
- **OpenStack Actions**: Extend `dashboard.html` and `routes.py` to list instances, create VMs, manage networks, etc.

---

## 🐳 Docker Support (Optional)

Use `docker-compose.yml` to run the app and Redis together:

```yaml
version: '3.8'
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    depends_on:
      - redis
    volumes:
      - ./config/.env:/app/config/.env
```

Build and run:
```bash
docker-compose up --build
```

> Make sure to create a `Dockerfile` if needed (see Tips below).

---

## 🔐 Security Best Practices

- 🔒 Always use HTTPS in production (OAuth requires secure redirect URIs).
- 🗝️ Store secrets in `.env` and never commit them.
- 🔄 Rotate `SECRET_KEY` periodically.
- 🛡️ Validate and sanitize all user inputs and OpenStack responses.
- 🧼 Clear Redis sessions on logout.

---

## 🛠️ Extending the Project

You can extend this app to:

- List and manage OpenStack instances, networks, volumes.
- Add role-based access control (RBAC).
- Support multiple identity providers (e.g., GitHub, Microsoft).
- Deploy on Kubernetes or cloud platforms.
- Add logging, monitoring, and error tracking.

---

## 📚 Dependencies

- `Flask`: Web framework
- `Authlib`: OAuth 2.0 client for Google SSO
- `python-openstacksdk`: Unified API for OpenStack
- `redis`: Redis client for session storage
- `python-dotenv`: Environment variable management
- `Flask-Session`: Server-side session support

Install them with:
```bash
pip install -r requirements.txt
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙌 Author

**Sumon Paul**  
📧 sumonpaul461@gmail.com  
🔗 [GitHub Profile](https://github.com/SumonPaul18)

---

## 💬 Feedback & Contributions

Contributions, issues, and feature requests are welcome!  
Feel free to check [issues page](https://github.com/SumonPaul18/openstack-python/issues) or contact the author.

> Show some ❤️ by starring the repo!

```

---

## ✅ Final Notes

### Recommendations to Improve the Repo Further:
1. ✅ Add a `LICENSE` file if not already present.
2. ✅ Add a `Dockerfile` for containerization.
3. ✅ Include logging and error handling in routes.
4. ✅ Add unit tests (`tests/` folder with pytest).
5. ✅ Use GitHub Actions for CI/CD (e.g., test on push).
6. ✅ Add screenshots of the login/dashboard in README (optional but helpful).

Let me know if you'd like me to generate:
- A `Dockerfile`
- GitHub Actions CI workflow
- Unit tests
- Dashboard enhancements

And I’ll help you make this project truly production-ready. 🚀
