"""
Populate the database with an admin account, a few sample jobs, a partner
agency, and one example CV profile — so you have something to click through
right after setup.

Usage:
    flask db upgrade      # create tables first
    python seed.py
"""
from datetime import date
from app import create_app
from app.extensions import db
from app.models import User, Applicant, Employer, Job, Partner, CVProfile

app = create_app()

with app.app_context():
    db.create_all()

    if not User.query.filter_by(email="admin@asmagency.com").first():
        admin = User(name="Head Admin", username="admin", email="admin@asmagency.com", phone="+251900000000",
                     role="admin", is_verified=True, is_super_admin=True)
        admin.set_password("ChangeMe123!")
        db.session.add(admin)
        print("Created super admin -> username 'admin' / ChangeMe123!  (change this password immediately)")

    # --- named staff admin accounts, each with a distinct, limited permission set
    #     (demonstrates granular roles) — idempotent: safe to re-run, never creates duplicates ---
    staff_admins = [
        {"name": "Tofik", "username": "tofik", "email": "tofik@asmagency.com", "phone": "+251900000001",
         "permissions": ["applicants", "documents", "cv"]},
        {"name": "Seid", "username": "seid", "email": "seid@asmagency.com", "phone": "+251900000002",
         "permissions": ["jobs", "partners", "interviews"]},
        {"name": "Alima", "username": "alima", "email": "alima@asmagency.com", "phone": "+251900000003",
         "permissions": ["payments", "reviews", "notifications"]},
    ]
    for staff in staff_admins:
        exists = User.query.filter(
            (User.email == staff["email"]) | (User.phone == staff["phone"]) | (User.username == staff["username"])
        ).first()
        if exists:
            print(f"Skipped {staff['name']} — an account with this email/phone/username already exists.")
            continue
        staff_user = User(name=staff["name"], username=staff["username"], email=staff["email"], phone=staff["phone"],
                          role="admin", is_verified=True, permissions=staff["permissions"])
        staff_user.set_password("ChangeMe123!")
        db.session.add(staff_user)
        print(f"Created admin -> username '{staff['username']}' / ChangeMe123!  (permissions: {', '.join(staff['permissions'])})")

    if not Employer.query.filter_by(company_name="Al Falah General Trading").first():
        e1 = Employer(company_name="Al Falah General Trading", country="UAE", city="Dubai", is_verified=True)
        e2 = Employer(company_name="Riyadh Home Services Co.", country="Saudi Arabia", city="Riyadh", is_verified=True)
        db.session.add_all([e1, e2])
        db.session.flush()

        jobs = [
            Job(employer_id=e1.id, title_am="የቤት ውስጥ ሰራተኛ", title_en="Domestic Worker",
                description_am="የቤት ውስጥ አጠቃላይ ስራዎች።", description_en="General household duties.",
                category="Domestic Work", country="UAE", positions_available=5),
            Job(employer_id=e1.id, title_am="የሆቴል ሰራተኛ", title_en="Hotel Staff",
                description_am="የሆቴል አገልግሎት ስራዎች።", description_en="Hospitality service roles.",
                category="Hospitality", country="UAE", positions_available=3),
            Job(employer_id=e2.id, title_am="የጽዳት ሰራተኛ", title_en="Cleaning Staff",
                description_am="የቢሮ እና የመኖሪያ ጽዳት።", description_en="Office and residential cleaning.",
                category="Cleaning", country="Saudi Arabia", positions_available=8),
        ]
        db.session.add_all(jobs)
        print("Added sample employers and job postings.")

    if not Partner.query.filter_by(name="Gulf Horizon Recruitment").first():
        partner = Partner(
            name="Gulf Horizon Recruitment", country="UAE",
            contact_person="Ahmed Al Mansoori", contact_email="contact@gulfhorizon.example",
            contact_phone="+9715XXXXXXX",
        )
        db.session.add(partner)
        print("Added a sample partner agency.")

    db.session.commit()

    # --- one example applicant + CV profile so /admin/cv has something to show ---
    demo_email = "demo.applicant@example.com"
    demo_user = User.query.filter_by(email=demo_email).first()
    if not demo_user:
        demo_user = User(username="sample.applicant", email=demo_email, phone="+251911223344", role="applicant", is_verified=True)
        demo_user.set_password("Demo1234!")
        db.session.add(demo_user)
        db.session.flush()

        demo_applicant = Applicant(
            user_id=demo_user.id, full_name="Sample Applicant", gender="female",
            date_of_birth=date(2000, 5, 12), passport_number="E00000000",
            education_level="Secondary Complete", pipeline_status="matched",
        )
        db.session.add(demo_applicant)
        db.session.flush()

        demo_partner = Partner.query.first()
        demo_cv = CVProfile(
            applicant_id=demo_applicant.id, application_no="00001",
            post_applied_for="House Maid", monthly_salary=250, salary_currency="USD",
            contract_period_years=2, partner_id=demo_partner.id if demo_partner else None,
            religion="—", place_of_birth="Addis Ababa", marital_status="single",
            weight_kg=55, height_m=1.60,
            passport_issue_place="Addis Ababa", passport_issue_date=date(2024, 1, 1),
            passport_expiry_date=date(2029, 1, 1),
            languages=[{"language": "Arabic", "level": "fair"}, {"language": "English", "level": "good"}],
            skills=[
                {"skill": "Care of the Elderly", "level": "good"},
                {"skill": "Baby Sitting", "level": "good"},
                {"skill": "Cleaning", "level": "excellent"},
                {"skill": "Washing", "level": "excellent"},
                {"skill": "Cooking", "level": "good"},
            ],
            work_history=[{"period": "2021 - 2023", "country": "Lebanon"}],
            emergency_contact_name="Sample Contact", emergency_contact_phone="+251911000000",
        )
        db.session.add(demo_cv)
        db.session.commit()
        print("Added a demo applicant with a filled-in CV profile -> visible at /admin/cv")

    print("Seeding complete.")
