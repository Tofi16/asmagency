from flask_login import current_user
from app.extensions import db
from app.models.audit_log import AuditLog


def log_action(action, target_type=None, target_id=None, details=None):
    """
    Record an audit trail entry for the currently logged-in user.
    Best-effort: failures here should never break the calling request.
    """
    try:
        actor_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
        entry = AuditLog(
            actor_id=actor_id, action=action, target_type=target_type,
            target_id=target_id, details=details,
        )
        db.session.add(entry)
        # Deliberately not committing here — caller commits alongside their
        # own change so the log entry and the change land in one transaction.
    except Exception:
        pass
