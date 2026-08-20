import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present

from app import create_app
from app.extensions import db
from app.models import User, Applicant, Document, Employer, Job, Application, Payment

app = create_app(os.environ.get("FLASK_CONFIG", "development"))


@app.shell_context_processor
def make_shell_context():
    """Lets `flask shell` autoload models — handy for quick debugging."""
    return {
        "db": db, "User": User, "Applicant": Applicant, "Document": Document,
        "Employer": Employer, "Job": Job, "Application": Application, "Payment": Payment,
    }


if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
