from app.models import User


def test_register_creates_user_and_applicant(client, db):
    resp = client.post("/auth/register", data={
        "full_name": "Test Applicant",
        "email": "test@example.com",
        "phone": "+251911111111",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)

    assert resp.status_code == 200
    user = User.query.filter_by(email="test@example.com").first()
    assert user is not None
    assert user.applicant is not None
    assert user.applicant.full_name == "Test Applicant"
    assert user.applicant.pipeline_status == "registered"


def test_login_wrong_password_fails(client, db):
    user = User(email="a@b.com", phone="+251900000001", role="applicant")
    user.set_password("correct-password")
    db.session.add(user)
    db.session.commit()

    resp = client.post("/auth/login", data={
        "email": "a@b.com", "password": "wrong-password",
    }, follow_redirects=True)

    assert b"Incorrect email or password" in resp.data or "የተሳሳተ".encode() in resp.data


def test_dashboard_requires_login(client):
    resp = client.get("/applicant/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 401)
