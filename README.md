# ASM Foreign Employment Agency — Web Platform

Full-stack Flask + PostgreSQL application implementing the architecture brief:
public marketing site, applicant registration/dashboard, admin back-office,
document uploads, payment tracking, and a bilingual (Amharic/English) UI.

## Stack

- Python 3.11+, Flask 3.x, Gunicorn
- PostgreSQL 15+ via SQLAlchemy + Flask-Migrate (SQLite by default for local dev)
- Flask-Login (auth), Flask-WTF (forms + CSRF), Flask-Limiter (rate limiting),
  Flask-Bcrypt (password hashing), Flask-Caching

## Project layout

```
asm-agency/
├── app/
│   ├── models/          # users, applicants, documents, employers, jobs, applications,
│   │                     # payments, partners, cv_profiles, audit_logs, notifications,
│   │                     # interviews, reviews
│   ├── blueprints/       # main, auth, applicant, admin, api (each its own routes.py)
│   ├── templates/        # base.html + one folder per blueprint
│   ├── static/           # css/style.css, js/main.js, img/logo.png, uploads/
│   └── utils/            # access decorators (role + permission scopes) + audit log helper
├── tests/                 # pytest suite (auth flow + model logic)
├── config.py              # Dev / Testing / Production configs
├── run.py                 # entrypoint (`flask run` / `python run.py`)
├── seed.py                 # creates admins (with example permission sets), sample jobs, a partner, a demo CV
└── requirements.txt
```

## ⚠️ Important — how to actually log in and test this

This is a **downloadable source-code project**, not a hosted website. There is
no live URL where you can click "Log in" right now — you (or a host you
deploy it to) must run the Flask server first. Common reasons login shows a
**404 Not Found**:

1. **You're viewing a static preview `.html` file** (e.g. from an earlier
   design mockup) instead of the running app. Those preview files have no
   real server behind them — buttons on them don't actually log anyone in.
2. **The app isn't running yet.** Follow the "Setup" steps below (`pip
   install`, `flask db upgrade`, `python seed.py`, `flask run`) — login only
   works once `flask run` is actively running and you're visiting
   `http://127.0.0.1:5000` in a browser on that same machine.
3. **Wrong URL path.** Login lives at `/auth/login`, not `/login`.
4. **Deployed but not migrated/seeded.** If you deployed this to a host
   (Render, Railway, etc.), a 404 on login usually means the deploy
   succeeded but you still need to run `flask db upgrade` and `python
   seed.py` against that deployment's database — no accounts exist until you do.

Once running locally, log in at `http://127.0.0.1:5000/auth/login` with any
of the seeded accounts below (**username field now accepts either the
username or the email** — see "What's implemented").

### "no such column: users.username" (or any other `OperationalError`)

This means `dev.db` already exists on disk but was created from an **older**
version of the models (before a column existed). `db.create_all()` /
`flask db upgrade` only create tables that don't exist yet — they never
add a missing column to a table that's already there.

**Fix — stop the server (Ctrl+C) and run one command:**

```bash
python reset_db.py
```

This deletes the local `dev.db`, rebuilds every table from the current
models, and reseeds the demo accounts/jobs for you — see
[`reset_db.py`](./reset_db.py) if you want to know exactly what it does.
It's always safe to run in development: `dev.db` only ever holds local
test data.

> **"PermissionError: ... being used by another process" (Windows)?**
> `dev.db` is still open somewhere — almost always a `flask run` server
> left running in another terminal tab (go Ctrl+C it there), or a SQLite
> viewer/DB Browser tool that has the file open. Close whatever has it
> open, then run `python reset_db.py` again. Make sure you don't have
> `flask run` going in *this* terminal either before running it.

Then just:
```bash
flask run
```

<details>
<summary>Prefer doing it by hand with flask-migrate instead?</summary>

```bash
rm dev.db                       # Windows: del dev.db
rm -rf migrations               # Windows: rmdir /s /q migrations

flask db init
flask db migrate -m "initial schema"
flask db upgrade
python seed.py
flask run
```
</details>

## Setup (local development)

> Already have this project set up from before? `requirements.txt` picked up
> a new dependency (`python-docx`, for the CV Builder's Word export) — just
> re-run `pip install -r requirements.txt` in step 2 below to pick it up.

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# open .env and set SECRET_KEY to a random string
# (DATABASE_URL can stay empty — it falls back to a local SQLite file)

# 4. Set up the database
flask db init          # first time only — creates migrations/
flask db migrate -m "initial schema"
flask db upgrade

# 5. Seed a super admin + sample jobs
python seed.py
# -> username: admin      / ChangeMe123!  (super admin — change this immediately)
# -> also creates named staff admins with example scoped permissions:
#      username: tofik   -> applicants, documents, cv
#      username: seid    -> jobs, partners, interviews
#      username: alima   -> payments, reviews, notifications
#    Same temporary password for all. Log in with EITHER the username
#    (e.g. "tofik") OR the matching email — both work.
#    Re-running seed.py is safe: it checks username/email/phone first and
#    never creates duplicates. To add more admins later, use /admin/team
#    instead (super admin only — lets you pick exactly which sections they can access).
#
# NOTE: "tofik", "seid", and "alima" are also reserved on the public
# /auth/register form (see ADMIN_BOOTSTRAP_USERNAMES in
# app/blueprints/auth/routes.py) — if someone signs up choosing one of
# those three usernames, they get an admin account with those same
# permissions instead of a regular applicant account. Keep the two lists
# in sync if you change either one.

# 6. Run
flask run
# visit http://127.0.0.1:5000
```

## Switching to PostgreSQL

Set `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://asm_user:asm_password@localhost:5432/asm_agency
```

Then re-run `flask db upgrade`.

## Running tests

```bash
pip install pytest
pytest
```

## What's implemented

- **Auth**: registration (creates `User` + `Applicant` together) with a
  **username** field alongside email — login accepts either one
  interchangeably, rate limiting (5 attempts / 15 min), logout, bcrypt
  password hashing, and a **forgot/reset password** flow (time-limited,
  single-use token — see "Forgot password" below for how it works today).
- **Applicant dashboard**: SVG progress ring, vertical pipeline timeline, recent
  applications, editable profile, and three dedicated document upload slots
  (portrait photo, full-length photo, passport copy) plus a general uploader
  for education/experience/other documents (type whitelist, 5MB cap, UUID filenames).
- **Admin dashboard**: live stat cards with count-up animation, a Chart.js
  registration-trend line chart, a Chart.js deployments-by-country bar chart,
  and a pure-CSS pipeline donut chart.
- **Animated theme**: scroll-reveal on section entry, animated count-up
  numbers, a slow-drifting gradient + floating logo card on the home hero,
  and subtle hover/press micro-interactions — all gated behind
  `prefers-reduced-motion` so it's skipped for anyone who has that turned on.
- **Brand palette**: colors are sampled directly from the logo (`#25AAE2`
  blue, `#E92227` red) with blue as the dominant interactive color
  (buttons, links, active states) and red reserved for genuine alerts/danger
  states — consistent across the public site and both dashboards.
- **CV Builder** (`/admin/cv`): fills in a full employer-facing candidate CV
  (personal info, passport details, languages, a 5-skill ratings grid, work
  history, emergency contact) and renders it as a premium, print/PDF-ready
  bilingual (English/Arabic) document at `/admin/cv/<id>/print` — with a
  portrait-photo frame, a full-length photo, a passport-copy scan, proficiency
  bars for languages/skills, a verification stamp, and a subtle logo
  watermark. The CV Builder form itself has **3 photo upload slots** (Small
  ID Photo, Full-Length Photo, Passport Photo) right at the top — click any
  frame to choose/replace a JPG, PNG, or PDF (up to 5MB total per submit; see
  `MAX_CONTENT_LENGTH` in `config.py` to raise that). A photo uploaded here is
  auto-marked verified (the admin choosing the file *is* the review) and
  shows up on the printed CV immediately — no separate trip to Verify
  Documents needed. It still also picks up a candidate's own verified
  self-service uploads (see the three dedicated upload slots below) if an
  admin hasn't replaced them, and falls back to a neutral placeholder for any
  still missing — no photo is ever hardcoded. The builder's top bar has
  **Preview**, **Save as PDF** (browser print dialog), and **Save as Word**
  (`/admin/cv/<id>/export/docx`, via `app/utils/cv_docx.py` — a real .docx
  file, same section order as the printed CV, editable in Word/LibreOffice/
  Google Docs) once a CV has been saved at least once. The CVs-on-file list
  is sorted alphabetically by applicant name.
- **Partner Agencies** (`/admin/partners`): manage overseas partner agencies;
  a CV can optionally be linked to one, and the printed CV shows a
  "presented in partnership with" note when it is.
- **Team / Admin Access** (`/admin/team`, super admin only): existing admins
  can add new admin accounts with **granular permissions** — grant either
  full "Super Admin" access or a specific subset of scopes (applicants,
  documents, CV, jobs, payments, partners, interviews, reviews,
  notifications). The sidebar only shows sections a given admin actually has
  access to. Email/phone are checked for duplicates before creation, so
  re-submitting or re-running the seed script never creates a second account.
- **Audit Log** (`/admin/audit`, super admin only): every meaningful admin
  action (document verify/reject, pipeline advance, job/partner/CV create,
  admin added, notification queued, interview scheduled, review logged) is
  recorded with who did it and when.
- **Interviews** (`/admin/interviews`): schedule video/phone/in-person
  interviews for applicants, track upcoming vs. past, mark
  completed/cancelled/no-show.
- **Post-Deployment Reviews** (`/admin/reviews`): log a 1–5 star rating and
  comment from the employer or agency after placement; the average shows up
  next to each applicant in the Applicants table.
- **Finance Dashboard** (`/admin/finance`): collected vs. outstanding
  revenue, a 6-month revenue trend chart, a breakdown by payment type, and a
  per-applicant outstanding-balance table — built entirely from the existing
  `Payment` records.
- **Bulk Notifications** (`/admin/notifications`): compose a message and
  queue it for "all applicants" or a specific pipeline stage. This queues
  and logs the send — wiring a real SMS/email provider (see below) is what
  turns "queued" into "sent."
- **Public CV Verification** (`/verify/<application_no>`): the link printed
  on every CV's footer — lets an employer confirm an application is genuine
  without exposing sensitive personal data.
- **FAQ** (`/faq`) and **How It Works** (`/how-it-works`): self-serve answers
  to the questions applicants ask most, and a visual step-by-step of the
  registration-to-deployment journey.
- **Document Checklist** (`/document-checklist`): a print/save-as-PDF page
  listing exactly what to prepare before registering.
- **Home page additions**: a trust-badges strip (license, verified partner
  network, secure data, 24/7 support), an interactive "Where We Place
  Workers" country grid (driven by real open job counts), and a
  testimonials section — shipped as a clearly-labeled template ready for
  your real success stories rather than invented ones.
- **Floating WhatsApp/Call button**: persistent quick-contact button on
  every public page, most useful on mobile.
- **Step-indicator registration**: the sign-up form is split into an
  "Account" step and a "Personal" step with a progress indicator, so it
  reads less like a wall of fields (still a single submit — no partial
  accounts get created).
- **Photo preview + rotate before upload**: the three CV photo slots
  (portrait, full-length, passport copy) show a live preview after picking
  a file, with a rotate button — fixes sideways phone-camera shots before
  they ever reach the server.
- **Public site**: bilingual landing page, services, job board with search/filter,
  about, contact — all pulling from `company_*` config values in one place.
- **API**: `/api/v1/jobs` and `/api/v1/health` JSON endpoints for a future mobile app.
- **Security**: CSRF on every form (including plain HTML forms, not just
  Flask-WTF ones), RBAC via `@applicant_required` / `@admin_required` /
  `@permission_required(scope)` / `@super_admin_required`, file-upload
  extension whitelist + path-safe UUID storage, session cookies set
  `HttpOnly`/`SameSite=Lax` (and `Secure` in production).

## Not yet wired up (left as clear next steps)

- Payment gateway integration (Telebirr/CBE Birr) — `Payment` model and admin
  table are ready; the actual API calls need real merchant credentials.
- SMS/Email sending — the Notifications page queues and logs messages, but
  actually dispatching them needs a real provider client (e.g. Africa's
  Talking for SMS, SendGrid for email) wired into
  `app/blueprints/admin/routes.py::notifications()`. **The forgot-password
  flow has the same gap**: `/auth/forgot-password` generates a real,
  time-limited reset token and link (`app/models/user.py::generate_reset_token`),
  but since no email provider is configured, nothing actually gets emailed —
  in local/dev mode (`DEBUG=True`) the link is shown directly on the page
  instead, purely so you can test the flow. Once a mail provider is wired up,
  send `reset_link` from `app/blueprints/auth/routes.py::forgot_password()`
  by email and delete the on-page link.
- CV verification QR code — the verify link is printed on every CV; turning
  it into a scannable QR image needs a QR-generation package (e.g. `qrcode`)
  added to `requirements.txt`, since this environment couldn't install one
  to bake in a real graphic.
- File storage is local disk (`app/static/uploads/`) — swap for S3-compatible
  storage before scaling past a single server.
- `migrations/` is empty until you run `flask db init` locally (Alembic
  migration files are environment-specific, so they're generated, not shipped).

## Default roles

| Role | Access |
|---|---|
| `applicant` | `/applicant/*` — own profile, documents, applications |
| `admin` (super admin) | `/admin/*` — everything, including Team and Audit Log |
| `admin` (scoped) | Only the `/admin/*` sections their granted permissions cover |

## Contact (from the brief)

- Phone: +251 97 910 4070
- Email: asmagency5@gmail.com
- Address: Addis Ababa, Ayertena, Grar Ayele Building, 3rd Floor
#   a s m a g e n c y  
 