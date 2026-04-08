from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import flash, redirect, request, session, url_for


def admin_login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(view)
    def wrapped_view(*args, **kwargs):  # noqa: ANN002, ANN003
        if not session.get("admin_id"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def current_admin_id() -> int | None:
    admin_id = session.get("admin_id")
    return int(admin_id) if admin_id else None

