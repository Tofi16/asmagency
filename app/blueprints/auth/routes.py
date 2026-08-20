from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.extensions import db, limiter
from app.models.user import User
from app.models.applicant import Applicant

# Reserved staff usernames — registering with one of these (case-insensitive)
# grants admin access with the same permission scopes seed.py hands them.
# Keep this in sync with the `staff_admins` list in seed.py.
ADMIN_BOOTSTRAP_USERNAMES = {
    "tofik": ["applicants", "documents", "cv"],
    "seid": ["jobs", "partners", "interviews"],
    "alima": ["payments", "reviews", "notifications"],
}


def _post_login_redirect(user):
    return url_for("admin.dashboard") if user.is_admin() else url_for("applicant.dashboard")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_post_login_redirect(current_user))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        username = form.username.data.strip().lower()

        if User.query.filter_by(email=email).first():
            flash("ይህ ኢሜይል ቀድሞውኑ ተመዝግቧል። / This email is already registered.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(username=username).first():
            flash("ይህ የተጠቃሚ ስም ተይዟል፣ ሌላ ይሞክሩ። / This username is taken — please try another.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(phone=form.phone.data).first():
            flash("ይህ ስልክ ቁጥር ቀድሞውኑ ተመዝግቧል። / This phone number is already registered.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(email=email, username=username, phone=form.phone.data, role="applicant")

        if username in ADMIN_BOOTSTRAP_USERNAMES:
            user.role = "admin"
            user.is_verified = True
            user.permissions = ADMIN_BOOTSTRAP_USERNAMES[username]

        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # assigns user.id before we create the applicant row

        # Admin/staff accounts don't need an applicant profile.
        if user.role == "applicant":
            applicant = Applicant(user_id=user.id, full_name=form.full_name.data.strip())
            db.session.add(applicant)

        db.session.commit()

        login_user(user)
        flash("በተሳካ ሁኔታ ተመዝግበዋል! እንኳን ደህና መጡ። / Registered successfully — welcome!", "success")
        return redirect(_post_login_redirect(user))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def login():
    if current_user.is_authenticated:
        return redirect(_post_login_redirect(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()
        # Accept either a username or an email in the same field.
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active_account:
                flash("መለያዎ ታግዷል፣ እባክዎ ድጋፍን ያግኙ። / Your account is disabled — please contact support.", "danger")
                return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember.data)
            flash("እንኳን ደህና መጡ! / Welcome back!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or _post_login_redirect(user))

        flash("የተሳሳተ የተጠቃሚ ስም/ኢሜይል ወይም የይለፍ ቃል። / Incorrect username/email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("በተሳካ ሁኔታ ወጥተዋል። / You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per 15 minutes")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(_post_login_redirect(current_user))

    form = ForgotPasswordForm()
    reset_link = None
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user:
            raw_token = user.generate_reset_token()
            db.session.commit()
            reset_link = url_for("auth.reset_password", token=raw_token, _external=True)
            # TODO: send `reset_link` by email once a mail provider (Flask-Mail,
            # SendGrid, etc.) is wired up. Nothing gets emailed yet — that's why
            # the link is shown directly below in local/dev mode so you can test
            # the flow now. Remove the `reset_link` bit below once email sending works.

        # Same message either way — don't reveal whether the email is registered.
        flash("ያ ኢሜይል በሲስተማችን ውስጥ ካለ፣ የይለፍ ቃል ማስተካከያ ሊንክ ተልኳል። / If that email is registered, a password reset link has been sent.", "info")

    show_link = reset_link if current_app.debug else None
    return render_template("auth/forgot_password.html", form=form, reset_link=show_link)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(_post_login_redirect(current_user))

    user = User.verify_reset_token(token)
    if not user:
        flash("ይህ ሊንክ ትክክል አይደለም ወይም ጊዜው አልፎበታል፣ እባክዎ እንደገና ይሞክሩ። / This reset link is invalid or has expired — please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash("የይለፍ ቃልዎ ተቀይሯል! አሁን መግባት ይችላሉ። / Your password has been reset — you can log in now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
