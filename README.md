## Foodie.

A secure, full-stack food-ordering platform built with Flask, featuring modern glass-style UI, SQLite persistence, and robust session-based authentication.

---

## Project Overview

Foodie is a comprehensive Flask-based web application designed to deliver a contemporary food delivery experience. The backend manages user authentication, session management, password security, rate limiting, role-based access control, RESTful order APIs, and SQLite data persistence with per-user order isolation. The frontend presents a sophisticated restaurant-style ordering interface with category navigation, restaurant discovery, dynamic menu modals, real-time cart management, interactive review carousel, responsive sidebar design, real-time notifications, theme customization, and persistent user-specific order history.

The application features full-stack architecture: server-side authentication and order data are persisted in SQLite with strict user isolation via foreign keys, while client-side cart data is maintained using browser-based `localStorage` for optimal UX during shopping.

## Core Features

### User Interface & Experience

- **Modern Design**: Glass-morphism styled responsive interface for authentication and ordering workflows
- **Theme Support**: Dynamic light and dark theme switching for enhanced user accessibility
- **Intuitive Navigation**: Dhaka-focused hero section with smooth, seamless navigation patterns
- **Product Browsing**: Comprehensive category system including pizza, burgers, noodles, bento, Mexican, healthy options, sushi, and desserts
- **Restaurant Discovery**: Featured restaurant showcase with interactive menu modals and detailed item selection
- **Cart Management**: Full-featured shopping cart with responsive 1/3-width sidebar (desktop) or fullscreen (mobile), quantity adjustments, item removal, real-time total calculation, and visual item count badges
- **Order Processing**: RESTful API endpoints for order creation and retrieval with CSRF protection and per-user data isolation
- **Order History**: Database-backed order tracking with user-specific isolation, displaying previous orders with itemized breakdowns, timestamps, restaurant source, and transaction totals via My Orders modal
- **Customer Reviews Carousel**: Auto-rotating review carousel with 5-star ratings, smooth 5-second auto-swipe transitions, interactive pagination dots, hover effects, and manual navigation
- **User Feedback**: Real-time toast notifications for cart modifications, item removal confirmations, empty state handling, and order confirmations
- **Interaction Design**: Scroll-reveal animations, keyboard navigation support (Escape key), and overlay-based modal dismissal
- **Resource Delivery**: Centralized favicon distribution through Flask routing

### Backend & Authentication

- Flask application with Jinja templates and RESTful API endpoints
- Signup and signin forms powered by Flask-WTF and WTForms
- CSRF protection on auth forms and API requests
- Flask-Login session handling with strong session protection
- Login by username or email with case-insensitive identifier matching
- Session lifetime set to 30 minutes with permanent session option
- Secure cookie options for HTTP-only, SameSite, and production-only secure cookies
- Auth route rate limiting with Flask-Limiter
- Account lockout after 5 failed password attempts
- Role-protected backend area for privileged users
- Authentication activity logging for account and session events

### Order Management API

- **GET /api/orders**: Retrieve authenticated user's complete order history with items and metadata
- **POST /api/orders**: Create and persist new order with CSRF validation and user ownership verification
- **Database-Backed Order Storage**: Orders stored in SQLite with relational schema (orders + order_items tables)
- **Per-User Data Isolation**: Foreign key constraints enforce user-specific data access, preventing cross-user order visibility
- **Transaction Safety**: All order operations use database transactions for consistency

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

### Server-Side Stored Data (SQLite)

SQLite stores the server-side account data needed for authentication, login state, roles, lockout status, auth activity logs, and persistent order history:

**Users Table**: `id`, `username`, `email`, `password_hash`, `role`, `is_locked`, `failed_attempts`, `created_at`

**Orders Table**: `id`, `user_id` (FK), `order_id`, `restaurant`, `total`, `cancelled`, `created_at`

**Order Items Table**: `id`, `order_id` (FK), `item_name`, `emoji`, `price`, `quantity`

### Client-Side Browser Storage

Browser-side `localStorage` is used for cart convenience during shopping:

| Key          | Purpose                                    |
| ------------ | ------------------------------------------ |
| `foodieCart` | Current cart items, quantities, and prices |

## Project Structure

```text
Foodie-delivery/
|-- .env                        # Environment variables (created locally)
|-- .gitignore                  # Git ignore rules
|-- README.md                   # This file
|-- .git/                       # Git repository
`-- files/
    |-- app.py                  # Flask app, routes, API endpoints, session management
    |-- database.py             # SQLite schema, user/order CRUD, auth logging
    |-- security.py             # Argon2 hashing, validation, sanitization
    |-- requirements.txt        # Python dependencies
    |-- foodie.db               # SQLite database (gitignored, created at runtime)
    `-- templates/
        |-- home.html           # Home page: categories, restaurants, cart, orders, reviews
        |-- signin.html         # Sign in form with glass-morphism styling
        |-- signup.html         # Sign up form with validation
        |-- admin.html          # Admin dashboard (role-protected)
        |-- error.html          # Error page template
        `-- favicon.png         # App favicon

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

### 3. Configure Environment Variables

Create a `.env` file in the project root with the following configuration:

```bash
# .env file
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-this-in-production
ADMIN_PATH=
DATABASE_PATH=files/foodie.db
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
LOG_LEVEL=INFO

```

**For production**, generate a strong SECRET_KEY:

```bash
python -c "import os; print(os.urandom(32).hex())"

```

### 4. Run the app

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

| Route          | Method    | Access         | Description                                                      |
| -------------- | --------- | -------------- | ---------------------------------------------------------------- |
| `/`            | GET       | Public         | Redirects authenticated users to `/home`, otherwise to `/signin` |
| `/signup`      | GET, POST | Public         | Displays signup form or creates new user account                 |
| `/signin`      | GET, POST | Public         | Displays signin form or logs users in by username or email       |
| `/home`        | GET       | Login required | Main food ordering experience with categories, restaurants       |
| `/logout`      | GET       | Login required | Logs out and clears the session                                  |
| `/favicon.png` | GET       | Public         | Serves the shared favicon                                        |
| `/api/orders`  | GET       | Login required | Returns authenticated user's order history as JSON               |
| `/api/orders`  | POST      | Login required | Creates and saves new order with CSRF protection                 |
| `/admin`       | GET       | Admin required | Admin dashboard with user management and auth logs               |

## How The App Works

### User Journey

1. **Registration**: A visitor signs up through the Flask-WTF signup form with username, email, and password
2. **Validation**: Backend validates input (username length, email format, password strength) and sanitizes with Bleach
3. **Account Creation**: Password is hashed with Argon2id and user is saved to SQLite
4. **Login**: User signs in with username or email and password
5. **Session**: Flask-Login creates a secure session (30-minute lifetime) and redirects to `/home`
6. **Browsing**: User explores categories (8 categories) or featured restaurants (6 restaurants)
7. **Menu Selection**: Clicking a category/restaurant opens a modal with food items
8. **Cart Management**: User adds items to cart; cart data stored in `localStorage` under `foodieCart`
9. **Review Section**: User sees rotating review carousel with 5-star customer testimonials (auto-swipes every 5 seconds)
10. **Order Placement**: User clicks "Place Order → "
11. **API Call**: Frontend sends POST to `/api/orders` with order data and CSRF token
12. **Database Save**: Backend validates user ownership and persists order to SQLite (orders + order_items tables)
13. **Confirmation**: Toast notification confirms order; cart is cleared
14. **Order History**: User views past orders from profile dropdown → "My Orders"
15. **API Retrieval**: Frontend fetches GET `/api/orders` to load user-specific orders
16. **Order Modal**: My Orders modal displays all orders with itemized details and totals

## Production Notes

- **Database**: SQLite is suitable for single-instance deployments. For high-traffic production, migrate to PostgreSQL, MySQL, or another hosted database
- **Scaling**: Flask-Limiter uses in-memory storage (suitable for single-instance). Use Redis for multi-process/distributed deployments
- **Environment Variables**: Store `.env` in a secure location; never commit to version control. Use managed secrets in production (AWS Secrets Manager, HashiCorp Vault, etc.)
- **SECRET_KEY**: Generate a strong random key with `python -c "import os; print(os.urandom(32).hex())"` for production
- **HTTPS**: Set `FLASK_ENV=production` to enable secure cookies (requires HTTPS proxy like Nginx)
- **Session Storage**: Flask sessions default to client-side signed cookies (no server storage needed); for cross-device sessions, use Flask-Session with Redis
- **Order Data**: Orders are now fully server-side with per-user isolation; cart remains client-side for UX during shopping
- **Monitoring**: Enable logging and set up alerts for failed login attempts and suspicious activity

## API Examples

### Retrieve User Orders

```bash
curl -X GET http://127.0.0.1:5000/api/orders \
  -H "Cookie: session=YOUR_SESSION_COOKIE"

# Response:
{
  "success": true,
  "orders": [
    {
      "id": "ORD217394",
      "timestamp": "2026-05-21 17:06:57",
      "restaurant": null,
      "items": [
        {"name": "Margherita", "emoji": "🍕", "price": 320, "qty": 1}
      ],
      "total": 320,
      "cancelled": 0
    }
  ]
}

```

### Create New Order

```bash
curl -X POST http://127.0.0.1:5000/api/orders \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: YOUR_CSRF_TOKEN" \
  -H "Cookie: session=YOUR_SESSION_COOKIE" \
  -d '{
    "order_id": "ORD123456",
    "restaurant": "Flame & Fork",
    "items": [
      {"name": "Grilled Chicken Steak", "emoji": "🔥", "price": 550, "qty": 1}
    ],
    "total": 550
  }'

# Response:
{
  "success": true,
  "message": "Order saved successfully"
}

```

## Author

Built by [CyberMythos](https://github.com/CyberMythos).
