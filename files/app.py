import os
import logging
import secrets
from datetime import timedelta
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, abort, send_from_directory, jsonify
)
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

from database import (
    init_db, create_user, get_user_by_username, get_user_by_email,
    get_user_by_id, update_last_login, increment_failed_attempts,
    log_auth_event, get_all_users, get_auth_logs, save_order,
    get_user_orders, delete_order
)
from security import (
    hash_password, verify_password, needs_rehash,
    validate_username, validate_email, validate_password,
    validate_login_identifier
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Generate and persist SECRET_KEY ───────────────────────────────────────────
def get_or_create_secret_key():
    """Get SECRET_KEY from environment or create and store it."""
    secret_key = os.environ.get("SECRET_KEY")
    if secret_key:
        return secret_key
    
    # Check if .env exists and has SECRET_KEY
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        # Try to read it again
        from dotenv import dotenv_values
        config = dotenv_values(env_file)
        if "SECRET_KEY" in config:
            return config["SECRET_KEY"]
    
    # Generate new key and save it to .env
    secret_key = secrets.token_hex(32)
    if not os.path.exists(env_file):
        with open(env_file, "w") as f:
            f.write(f"SECRET_KEY={secret_key}\n")
    else:
        # Append to existing .env
        with open(env_file, "a") as f:
            f.write(f"SECRET_KEY={secret_key}\n")
    
    logger.info("Generated and stored new SECRET_KEY in .env")
    return secret_key


app = Flask(__name__)
app.config.update(
    SECRET_KEY=get_or_create_secret_key(),
    WTF_CSRF_ENABLED=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    SESSION_COOKIE_SAMESITE="Strict",
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    WTF_CSRF_TIME_LIMIT=3600,
)

csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

login_manager = LoginManager(app)
login_manager.login_view = "signin"
login_manager.session_protection = "strong"

# ── Optional admin path from local environment ────────────────────────────────
ADMIN_PATH = os.environ.get("ADMIN_PATH", "").strip().strip("/")


# ── User model ────────────────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, data: dict):
        self.id = data["id"]
        self.username = data["username"]
        self.email = data["email"]
        self.role = data["role"]
        self.is_locked = bool(data.get("is_locked", False))

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    data = get_user_by_id(int(user_id))
    return User(data) if data else None


# ── WTForms (CSRF token carriers) ─────────────────────────────────────────────
class SignUpForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class SignInForm(FlaskForm):
    identifier = StringField("Username or Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


# ── Role decorator ────────────────────────────────────────────────────────────
def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Security headers ──────────────────────────────────────────────────────────
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://images.unsplash.com; "
        "script-src 'self' 'unsafe-inline';"
    )
    if os.environ.get("FLASK_ENV") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Even in production, add cache busting for static content with version
        response.headers["Cache-Control"] = "public, max-age=86400"
    else:
        # Development: Disable caching to always load latest updates
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/favicon.png")
def favicon():
    # Serve favicon.png from templates folder
    return send_from_directory(
        os.path.join(app.root_path, app.template_folder),
        "favicon.png",
        mimetype="image/png",
    )


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("signin"))


@app.route("/signup", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = SignUpForm()

    if request.method == "POST":
        if not form.validate_on_submit():
            return render_template("signup.html", form=form, error="Invalid CSRF token."), 400

        raw_username = request.form.get("username", "")
        raw_email = request.form.get("email", "")
        raw_password = request.form.get("password", "")

        ok, username = validate_username(raw_username)
        if not ok:
            return render_template("signup.html", form=form, error=username)

        ok, email = validate_email(raw_email)
        if not ok:
            return render_template("signup.html", form=form, error=email)

        ok, msg = validate_password(raw_password)
        if not ok:
            return render_template("signup.html", form=form, error=msg)

        if get_user_by_username(username) or get_user_by_email(email):
            return render_template("signup.html", form=form, error="Username or email already exists.")

        password_hash = hash_password(raw_password)
        success = create_user(username, email, password_hash)

        if success:
            log_auth_event("SIGNUP", username=username, ip_address=request.remote_addr)
            logger.info("New user registered: %s", username)
            return render_template("signup.html", form=form, success="Account created! Sign in now.")
        else:
            return render_template("signup.html", form=form, error="Registration failed. Try again.")

    return render_template("signup.html", form=form)


@app.route("/signin", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signin():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    form = SignInForm()

    if request.method == "POST":
        if not form.validate_on_submit():
            return render_template("signin.html", form=form, error="Invalid CSRF token."), 400

        raw_identifier = request.form.get("identifier", "")
        raw_password = request.form.get("password", "")

        ok, identifier = validate_login_identifier(raw_identifier)
        if not ok:
            return render_template("signin.html", form=form, error=identifier)

        # Lookup by username or email
        user_data = get_user_by_username(identifier) or get_user_by_email(identifier)

        if not user_data:
            log_auth_event("LOGIN_FAIL", username=identifier, ip_address=request.remote_addr, details="User not found")
            return render_template("signin.html", form=form, error="Invalid credentials.")

        if user_data["is_locked"]:
            log_auth_event("LOGIN_LOCKED", username=identifier, ip_address=request.remote_addr)
            return render_template("signin.html", form=form, error="Account locked. Contact support.")

        if not verify_password(user_data["password_hash"], raw_password):
            locked = increment_failed_attempts(user_data["username"])
            log_auth_event("LOGIN_FAIL", username=user_data["username"], ip_address=request.remote_addr,
                           details=f"Bad password. Attempts: {user_data['failed_attempts'] + 1}")
            if locked:
                return render_template("signin.html", form=form, error="Account locked after too many attempts.")
            return render_template("signin.html", form=form, error="Invalid credentials.")

        user = User(user_data)
        login_user(user, remember=False)
        session.permanent = True
        update_last_login(user.id)
        log_auth_event("LOGIN_SUCCESS", username=user.username, ip_address=request.remote_addr)
        logger.info("Login success: %s", user.username)

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("home"))

    return render_template("signin.html", form=form)


@app.route("/home")
@login_required
def home():
    return render_template("home.html", user=current_user)


@app.route("/logout")
@login_required
def logout():
    log_auth_event("LOGOUT", username=current_user.username, ip_address=request.remote_addr)
    logout_user()
    session.clear()
    return redirect(url_for("signin"))


# ── API Routes for Orders ─────────────────────────────────────────────────────
@app.route("/api/orders", methods=["GET"])
@login_required
def api_get_orders():
    """Fetch all orders for the current user"""
    try:
        orders = get_user_orders(current_user.id)
        # Format the response to match the frontend expectations
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": order['order_id'],
                "timestamp": order['created_at'],
                "restaurant": order['restaurant'],
                "items": order['items'],
                "total": order['total'],
                "cancelled": order['cancelled']
            })
        return jsonify({"success": True, "orders": formatted_orders})
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/orders", methods=["POST"])
@login_required
def api_save_order():
    """Save an order for the current user"""
    try:
        data = request.get_json()
        
        if not data or "order_id" not in data or "items" not in data:
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        order_id = data.get("order_id")
        items = data.get("items", [])
        restaurant = data.get("restaurant")
        total = data.get("total", 0)
        
        # Save to database
        success = save_order(current_user.id, order_id, items, restaurant, total)
        
        if success:
            return jsonify({"success": True, "message": "Order saved successfully"})
        else:
            return jsonify({"success": False, "error": "Failed to save order"}), 500
    except Exception as e:
        logger.error(f"Error saving order: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def admin_panel():
    users = get_all_users()
    logs = get_auth_logs(limit=50)
    log_auth_event("ADMIN_ACCESS", username=current_user.username, ip_address=request.remote_addr)
    return render_template("admin.html", users=users, logs=logs, user=current_user)


if ADMIN_PATH:
    app.add_url_rule(
        f"/{ADMIN_PATH}",
        "admin_panel",
        login_required(require_role("admin")(admin_panel)),
        methods=["GET"],
    )
else:
    logger.info("Admin panel route is disabled. Set ADMIN_PATH locally to enable it.")


# ── Error handlers ────────────────────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="Access denied."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@app.errorhandler(429)
def rate_limited(e):
    return render_template("error.html", code=429, message="Too many requests. Slow down."), 429


@app.errorhandler(500)
def server_error(e):
    logger.error("Server error: %s", e)
    return render_template("error.html", code=500, message="Something went wrong."), 500


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_ENV") != "production"
    # Bind to 0.0.0.0 to allow access from other machines on the network
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    app.run(debug=debug_mode, host=host, port=port)
