## Foodie. 

A secure, full-stack food-ordering platform built with Flask, featuring modern glass-style UI, SQLite persistence, and robust session-based authentication.

---

## Project Overview

Foodie is a comprehensive Flask-based web application designed to deliver a contemporary food delivery experience. The backend manages user authentication, session management, password security, rate limiting, role-based access control, and SQLite data persistence. The frontend presents a sophisticated restaurant-style ordering interface with category navigation, restaurant discovery, dynamic menu modals, cart management, real-time notifications, theme customization, and persistent order history.

The application is implemented as a polished demonstration platform: server-side authentication and user data are persisted in SQLite, while client-side cart and order history data are maintained using browser-based `localStorage`.

## Core Features

### User Interface & Experience

- **Modern Design**: Glass-morphism styled responsive interface for authentication and ordering workflows
- **Theme Support**: Dynamic light and dark theme switching for enhanced user accessibility
- **Intuitive Navigation**: Dhaka-focused hero section with smooth, seamless navigation patterns
- **Product Browsing**: Comprehensive category system including pizza, burgers, noodles, bento, Mexican, healthy options, sushi, and desserts
- **Restaurant Discovery**: Featured restaurant showcase with interactive menu modals and detailed item selection
- **Cart Management**: Full-featured shopping cart with quantity adjustments, item removal, real-time total calculation, and visual item count badges
- **Order Processing**: Order confirmation workflow with local demo persistence
- **Order History**: Comprehensive order tracking interface displaying previous orders with itemized breakdowns, source restaurant/category information, and transaction totals
- **User Feedback**: Real-time toast notifications for cart modifications, item removal confirmations, empty state handling, and order confirmations
- **Interaction Design**: Scroll-reveal animations, keyboard navigation support (Escape key), and overlay-based modal dismissal
- **Resource Delivery**: Centralized favicon distribution through Flask routing

### Backend & Authentication

- Flask application with Jinja templates
- Signup and signin forms powered by Flask-WTF and WTForms
- CSRF protection on auth forms
- Flask-Login session handling with strong session protection
- Login by username or email
- Session lifetime set to 30 minutes
- Secure cookie options for HTTP-only, SameSite, and production-only secure cookies
- Auth route rate limiting with Flask-Limiter
- Account lockout after 5 failed password attempts
- Role-protected backend area for privileged users
- Authentication activity logging for account and session events

### Security

- Argon2id password hashing through `argon2-cffi`
- Password verification without storing plaintext passwords
- Password strength validation: minimum length, uppercase, lowercase, and digit
- Username, email, and login identifier sanitization with Bleach
- Input validation for username length, email format, and password length
- Security response headers:
  - `X-Content-Type-Options`
  - `X-Frame-Options`
  - `X-XSS-Protection`
  - `Referrer-Policy`
  - `Content-Security-Policy`
  - `Strict-Transport-Security` in production

## Tech Stack

| Layer                 | Technology                             |
| --------------------- | -------------------------------------- |
| Backend               | Python, Flask                          |
| Authentication        | Flask-Login, Flask-WTF, WTForms        |
| Password Security     | Argon2id via `argon2-cffi`             |
| Rate Limiting         | Flask-Limiter                          |
| Data Sanitization     | Bleach                                 |
| Database              | SQLite                                 |
| Frontend              | Jinja, HTML, CSS, vanilla JavaScript   |
| Local Browser Storage | `localStorage` for cart and orders     |
| Config                | `python-dotenv`, environment variables |

## Database Design

The backend uses SQLite through [files/database.py](./files/database.py). On startup, `init_db()` prepares the local database tables. Runtime database files are local artifacts and should not be committed.

### Stored Data

SQLite stores the server-side account data needed for authentication, login state, roles, lockout status, and auth activity logs.

Browser-side data is only used for demo ordering convenience:

| Key            | Purpose                                    |
| -------------- | ------------------------------------------ |
| `foodieCart`   | Current cart items, quantities, and prices |
| `foodieOrders` | Local order history displayed in My Orders |

## Project Structure

```text
Foodie/
|-- README.md
`-- files/
    |-- app.py                  # Flask app, routes, forms, sessions, security headers
    |-- database.py             # SQLite connection, schema, user queries, auth logs
    |-- security.py             # password hashing, validation, sanitization
    |-- requirements.txt        # Python dependencies
    |-- .gitignore
    `-- templates/
        |-- admin.html          # role-protected admin overview
        |-- error.html          # custom error page
        |-- favicon.png         # app favicon/logo
        |-- home.html           # ordering UI, cart, menus, local order history
        |-- signin.html         # signin page
        `-- signup.html         # signup page

```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/CyberMythos/Foodie.git
cd Foodie

```

### 2. Set up Virtual Environment & Install Dependencies

Choose the step-by-step setup guide based on your Operating System:

#### 🐧 Linux / 🍏 macOS

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required packages
pip install -r files/requirements.txt

```

#### 🪟 Windows

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment (Command Prompt / CMD)
venv\Scripts\activate

# OR if you are using PowerShell:
# .\venv\Scripts\Activate.ps1

# Install the required packages
pip install -r files/requirements.txt

```

### 3. Run the app

Make sure your virtual environment is active (you will see `(venv)` at the beginning of your terminal line), then run:

```bash
cd files
python app.py

```

Open the app in your browser:

```text
http://127.0.0.1:5000

```

## Route Map

| Route | Access | Description |
| --- | --- | --- |
| `/` | Public | Redirects authenticated users to `/home`, otherwise to `/signin` |
| `/signup` | Public | Creates a new user account |
| `/signin` | Public | Logs users in by username or email |
| `/home` | Login required | Main food ordering experience |
| `/logout` | Login required | Logs out and clears the session |
| `/favicon.png` | Public | Serves the shared favicon |

## How The App Works

1. A visitor signs up through the Flask-WTF signup form.
2. The backend validates and sanitizes input, hashes the password with Argon2id, and saves the user in SQLite.
3. The user signs in with a username or email.
4. Flask-Login creates a secure session and redirects the user to `/home`.
5. The user browses categories or restaurants, opens menu modals, and adds items to the cart.
6. Cart data is saved in `localStorage` under `foodieCart`.
7. Placing an order creates a local order record under `foodieOrders`.
8. The user can view order history from the profile dropdown.

## Production Notes

* SQLite is currently used directly. For production deployment, use a persistent disk/volume or migrate the database layer to a hosted database.
* Flask-Limiter currently uses in-memory storage. Use Redis or another shared limiter backend for multi-process or production deployments.
* Keep local configuration files private and never publish real configuration values.
* `FLASK_ENV=production` enables secure cookies and HSTS behavior.
* Cart and order history are browser-side demo features. Move them to backend tables if you want real cross-device order management.

## Author

Built by [CyberMythos](https://github.com/CyberMythos).
