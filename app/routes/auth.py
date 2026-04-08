from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError, ValidationError

bp = Blueprint("auth", __name__, url_prefix="/admin")
auth_service = AuthService()


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        try:
            admin = auth_service.login(
                username=username,
                password=password,
                ip=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            session["admin_full_name"] = admin["full_name"]
            session.permanent = True
            next_path = request.args.get("next")
            return redirect(next_path or url_for("admin.dashboard"))
        except (AuthenticationError, ValidationError) as exc:
            flash(str(exc), "error")

    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    admin_id = session.get("admin_id")
    if admin_id:
        auth_service.logout(
            admin_id=int(admin_id),
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
    session.clear()
    flash("Signed out successfully.", "success")
    return redirect(url_for("auth.login"))

