import os
import traceback

from flask import Flask, jsonify

startup_error = None


def _fallback_app():
	fallback = Flask(__name__)

	@fallback.route("/health")
	def health():
		if startup_error:
			return jsonify({"status": "error", "startup_error": startup_error}), 503
		return jsonify({"status": "ok"})

	@fallback.route("/")
	@fallback.route("/<path:path>")
	def fallback(path=""):
		return jsonify({"status": "ok", "message": "App is starting"}), 200
	return fallback

try:
	from app import create_app

	app = create_app(os.environ.get("FLASK_CONFIG") or "production")
except Exception:  # pragma: no cover - protects the serverless module import
	startup_error = traceback.format_exc()
	traceback.print_exc()
	app = _fallback_app()
