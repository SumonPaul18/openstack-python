```markdown
# OpenStack Cloud Management Portal with Google & Email Authentication

A Flask-based web application that integrates **OpenStack cloud management** with **Google OAuth** and **email/password authentication**. This portal automatically provisions OpenStack users and projects upon user signup, enabling a seamless cloud experience similar to AWS or GCP.

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![OpenStack](https://img.shields.io/badge/OpenStack-187BFF?style=for-the-badge&logo=openstack&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

---

## 🌟 Features

- ✅ **User Authentication**
  - Google Sign-In via OAuth 2.0
  - Email & Password Registration with confirmation
  - Password reset functionality
- ✅ **OpenStack Integration**
  - Automatic **OpenStack user** creation on signup
  - Automatic **project (tenant)** creation
  - User assigned as `member`, admin assigned as `admin` of the project
  - Default project set for each user
- ✅ **Session Management**
  - Redis-backed session storage for scalability
  - Secure session handling with Flask-Session
- ✅ **Email Confirmation & Reset**
  - Email sent via Gmail SMTP
  - Token-based confirmation and password reset
- ✅ **Dashboard Access**
  - Protected dashboard for authenticated users
  - Future-ready for cloud resource display (VMs, Networks, Volumes)

---

## 🛠️ Technology Stack

| Layer | Technology |
|------|------------|
| **Backend** | Python, Flask |
| **Database** | SQLite (Flask-SQLAlchemy) |
| **Authentication** | Flask-Login, Flask-Dance (Google OAuth) |
| **Session Storage** | Redis |
| **Email** | Flask-Mail (Gmail SMTP) |
| **OpenStack SDK** | openstacksdk |
| **Frontend** | HTML, CSS, JavaScript, Bootstrap |
| **Environment** | `.env` file for secrets |

---

## 📁 Project Structure

```
openstack-flask-gmsso-redis/
├── .env                    # Environment variables
├── app.py                  # Application entry point
├── main.py                 # Core logic: auth, OpenStack integration
├── dashboard.py            # Dashboard routes
├── requirements.txt        # Python dependencies
├── clouds.yaml             # OpenStack cloud configuration
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── templates/
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── reset_password.html
    └── ...                 # Other HTML templates

```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/openstack-flask-gmsso-redis.git
cd openstack-flask-gmsso-redis
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```env
SECRET_KEY=your_flask_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
OAUTHLIB_RELAX_TOKEN_SCOPE=1
OAUTHLIB_INSECURE_TRANSPORT=1
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=True
MAIL_USE_SSL=False
REDIS_HOST=192.168.0.207
```

> 🔐 Use Gmail App Password for `MAIL_PASSWORD` if 2FA is enabled.

### 5. Create OpenStack Configuration

Create `clouds.yaml` in the project root:

```yaml
clouds:
  openstack:
    auth:
      auth_url: http://192.168.0.200:5000/v3
      username: admin
      password: your_admin_password
      project_name: admin
      user_domain_name: Default
      project_domain_name: Default
    region_name: RegionOne
    interface: public
    identity_api_version: 3
```

### 6. Initialize the Database

```bash
python app.py --setup
```

### 7. Run the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🔐 Usage

| Action | Description |
|-------|-------------|
| **Sign Up** | Use email & password or Google to register |
| **Email Confirmation** | Click the link in the confirmation email |
| **Login** | Use registered credentials or Google |
| **Password Reset** | Use "Forgot Password?" link on login page |
| **Dashboard** | View your cloud services (future) |

---

## 🔧 OpenStack Integration Logic

When a user signs up:
1. A new **OpenStack user** is created with the user's email.
2. A new **project** is created (e.g., `project_1`).
3. The user is assigned the `member` role in the project.
4. The OpenStack `admin` user is assigned the `admin` role in the project.
5. The project is set as the user's **default project**.
6. User's OpenStack IDs are stored in the database for future access.

All this happens transparently — the user only interacts with the web portal.

---

## 📈 Future Enhancements (Planned)

- 🖥️ Display OpenStack VMs, Networks, and Volumes in the dashboard
- 🔄 Auto-login to Horizon (OpenStack Dashboard) via token
- 💳 Billing system based on resource usage
- 🔐 Role-based access control (RBAC)
- 📊 Real-time monitoring and metrics
- 🌐 Microservices architecture for scalability

---

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Submit bug reports
- Suggest new features
- Open pull requests

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## ✉️ Contact

For questions or support, contact:
- **Name**: Sumon Paul
- **Email**: sumonpaul267@gmail.com
- **GitHub**: [github.com/sumonpaul](https://github.com/sumonpaul)

---

> 🚀 **Empowering cloud access with simplicity and security.**