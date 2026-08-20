from app.models import Applicant, User


def test_pipeline_progress_percent(app, db):
    user = User(email="p@test.com", phone="+251900000002", role="applicant")
    user.set_password("password123")
    db.session.add(user)
    db.session.flush()

    applicant = Applicant(user_id=user.id, full_name="Progress Test")
    db.session.add(applicant)
    db.session.commit()

    assert applicant.pipeline_status == "registered"
    assert applicant.pipeline_progress_percent() == round(1 / 7 * 100)

    applicant.pipeline_status = "deployed"
    assert applicant.pipeline_progress_percent() == 100
