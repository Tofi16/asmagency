import os

try:
    from app import create_app
except Exception:  # pragma: no cover
    create_app = None

if create_app is not None:
    app = create_app(os.environ.get("FLASK_CONFIG") or "production")
else:
    from flask import Flask, jsonify

    app = Flask(__name__)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/")
    @app.route("/<path:path>")
    def fallback(path=""):
        return jsonify({"status": "ok", "message": "App is starting"}), 200
