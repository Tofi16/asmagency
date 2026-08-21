import os
import traceback

from flask import Flask, jsonify


app = Flask(__name__)
startup_error = None


@app.route("/health")
def health():
	if startup_error:
		return jsonify({"status": "error", "startup_error": startup_error}), 503
	return jsonify({"status": "ok"})


@app.route("/")
@app.route("/<path:path>")
def fallback(path=""):
	return jsonify({"status": "ok", "message": "App is starting"}), 200


try:
	from app import create_app

	app = create_app(os.environ.get("FLASK_CONFIG") or "production")
except Exception:  # pragma: no cover - protects the serverless module import
	startup_error = traceback.format_exc()
	traceback.print_exc()
