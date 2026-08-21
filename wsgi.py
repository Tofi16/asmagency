import os
import traceback

from flask import Flask, jsonify


app = Flask(__name__)


@app.route("/health")
def health():
	return jsonify({"status": "ok"})


@app.route("/")
@app.route("/<path:path>")
def fallback(path=""):
	return jsonify({"status": "ok", "message": "App is starting"}), 200


try:
	from app import create_app

	app = create_app(os.environ.get("FLASK_CONFIG") or "production")
except Exception:  # pragma: no cover - protects the serverless module import
	traceback.print_exc()
