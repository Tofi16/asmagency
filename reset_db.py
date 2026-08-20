"""
One-command local dev database reset.

Run this any time you see a database error such as:
    sqlalchemy.exc.OperationalError: no such column: users.username
    sqlalchemy.exc.OperationalError: no such column: users.reset_token_hash

That error means dev.db already exists on disk but was built from an
OLDER version of the models. Flask-SQLAlchemy's create_all() (and
`flask db upgrade` without a matching migration) only creates tables
that don't exist yet — neither one ever adds a missing column to a
table that's already there.

This script deletes the local dev.db, rebuilds every table from the
CURRENT models, and reseeds the demo data — one command instead of
several manual steps.

Usage:
    python reset_db.py

Safe to run any time in development: dev.db only ever holds local
test data, never anything real. Do NOT run this against a production
database (it only touches SQLite files referenced by dev DATABASE_URL
anyway, so it's a no-op against Postgres/MySQL).
"""
import os
import sys
import time
import runpy

from app import create_app
from app.extensions import db

app = create_app(os.environ.get("FLASK_CONFIG", "development"))

db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
if db_uri.startswith("sqlite:///"):
    db_path = db_uri.replace("sqlite:///", "", 1)
    if os.path.exists(db_path):
        deleted = False
        last_error = None
        for attempt in range(3):
            try:
                os.remove(db_path)
                deleted = True
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.5)  # a server that's mid-shutdown can release the lock a moment later

        if deleted:
            print(f"Deleted {db_path}")
        else:
            print(f"\nCouldn't delete {db_path} — it's still open in another program.\n")
            print("On Windows this almost always means one of:")
            print("  1. A `flask run` server is still running in another terminal")
            print("     (switch to it and press Ctrl+C to stop it), or")
            print("  2. Some other tool has dev.db open right now — e.g. DB Browser")
            print("     for SQLite, a VS Code SQLite-viewer extension, or a second")
            print("     `python`/`flask shell` session — close it.")
            print("\nThen run `python reset_db.py` again.")
            print(f"\n(underlying error: {last_error})")
            sys.exit(1)
    else:
        print(f"No existing {db_path} found — creating fresh.")
else:
    print("Not using a local SQLite file — skipping delete step. "
          "If this is Postgres/MySQL, drop/recreate that database yourself first.")

with app.app_context():
    db.create_all()
    print("Created all tables from the current models.")

print("\nSeeding demo data...\n")
runpy.run_path("seed.py", run_name="__main__")
