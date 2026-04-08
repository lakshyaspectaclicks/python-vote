import logging
import os
from pathlib import Path

from flask import Flask, redirect, render_template, send_from_directory, url_for
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

from config import CONFIG_MAP
from app.utils.db import db

csrf = CSRFProtect()


def _configure_logging(app: Flask) -> None:
    level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def create_app(config_name: str | None = None) -> Flask:
    load_dotenv()
    selected = config_name or os.getenv("FLASK_ENV", "development")
    config_class = CONFIG_MAP.get(selected, CONFIG_MAP["development"])

    app = Flask(__name__)
    app.config.from_object(config_class)

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    _configure_logging(app)
    db.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.voting import bp as voting_bp
    from app.routes.exports import bp as export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voting_bp)
    app.register_blueprint(export_bp)

    @app.route("/")
    def home():
        return redirect(url_for("voting.index"))

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.errorhandler(404)
    def not_found(error):  # noqa: ANN001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):  # noqa: ANN001
        app.logger.exception("Unhandled server error: %s", error)
        return render_template("errors/500.html"), 500

    @app.context_processor
    def inject_common():
        return {"school_name": app.config.get("SCHOOL_NAME")}

    from app.services.auth_service import AuthService

    @app.cli.command("create-admin")
    def create_admin_command():
        username = input("Username: ").strip()
        full_name = input("Full name: ").strip()
        password = input("Password: ").strip()
        auth_service = AuthService()
        admin_id = auth_service.create_admin(username=username, full_name=full_name, password=password)
        print(f"Created admin #{admin_id} ({username})")

    return app
