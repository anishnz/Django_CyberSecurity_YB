# CyberQuest (Django)

**Learn. Play. Decide. Stay Cyber Safe.**

CyberQuest is a cyber-safety learning platform for New Zealand schools. Students study short topics, practise with
instant feedback, sit level exams and earn certificates. Teachers assign exams and read class reports. School Admins
run classes, students and the licence. The Super Admin runs the whole platform.

This version is the Django rebuild of the team's earlier Flask prototype, made for **MSE800 Professional Software
Engineering – Assessment 2** at Yoobee College of Creative Innovation (lecturer: Dr. Farah Younas).

| | |
|---|---|
| Project code | `` |
| Simulated company | Mount Everest Digital Limited |
| Version | 1.1.0 |
| Repository | https://github.com/anishnz/Django_CyberSecurity_YB |

> **Simulation note.** The company, client, schools, students, payments and Māori advisers in the demo data are
> made up for this college project. No real student data is used. Demo bank numbers and payslips are marked "demo".

---

## 1. Team

| Student | ID | Role in the team | Main parts of the code |
|---|---|---|---|
| Anish Shrestha | 270889991 | Lead Software Engineer, system designer | accounts, roles, security, Login as, MFA, password reset, AI drafts, settings, Docker and run scripts |
| Rajneesh Kumar | 270245010 | Backend and database developer | schools, licensing, payments, help desk rules, emails, announcements, notifications |
| Dinesh Upreti | 270830269 | Frontend developer and business analyst | public website, student and teacher screens, reports and BI, certificates, help centre, display options |
| Jihe Qi | 27008116 | QA Lead, integrations, meeting secretary | automated tests, Pylint, integrations vault, AI test page, media library, upload checks, demo data |

Every member also wrote code in the other areas and reviewed each other's pull requests (see the Git history:
`feature/<name>-<feature>` branches merged into `develop`).

---

## 2. Run it

### Windows – one double-click (Docker)

1. Install **Docker Desktop** and start it.
2. Double-click **`run.bat`**. It:
   - checks Docker is running,
   - finds a **free port** (8000, or the next free port up to 8020) so it never clashes with another program,
   - creates `.env` with random secrets on the first run,
   - stops an older CyberQuest container first, so the same port is used again (your data is kept in Docker volumes),
   - starts the container, waits for `/health/`, and opens your browser.
3. Stop it with `docker compose down`.

### Windows without Docker

Double-click **`run_local.bat`** (needs Python 3.10 or newer). It:

- checks Python 3.10+ and finds a **free port** (8000, or the next free port up to 8020),
- makes a virtual environment and installs the packages – only the first time, or when `requirements.txt`
  changes, so later starts also work with **no internet**,
- creates `.env` with random secrets on the first run, prepares the database and loads the demo data,
- starts the **waitress** server and opens your browser **when CyberQuest answers** on `/health/`.

Keep the black window open; press **Ctrl + C** to stop.

### Open CyberQuest in your browser

1. Look in the black window for: `CyberQuest is starting at http://127.0.0.1:8000/` (the number can be 8001 or
   higher when 8000 was busy).
2. The browser opens by itself. If not, type that address into the browser.
3. Demo logins: `http://127.0.0.1:<port>/accounts/demo-accounts/`. `localhost` and `127.0.0.1` mean the same thing –
   your own computer.

### Mac / Linux

```bash
./run.sh                 # Docker, same free-port check
# or by hand:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

### Demo logins

Open **`/accounts/demo-accounts/`** (only shown while `DEMO_MODE=1`). The main ones:

| Role | Username | Password |
|---|---|---|
| Super Admin | `superadmin` | `Everest@2026` |
| School Admin | `admin.brightstar` | `Admin@2026` |
| Teacher | `sione.faleolo` | `Teacher@2026` |
| Teacher + Cultural Guide (Kaiārahi) | `jane.wilson` | `Teacher@2026` |
| Student | `tama.ngata` | `Kiaora@2026` |
| Student (Nepal demo school) | `bikash.thapa` | `Namaste@2026` |
| Demo Guest (read only) | button on the login page | – |

The Super Admin can also use **Login as** to open any dashboard. A red bar shows who you are viewing as, and every
Login as is written to the security log.

---

## 3. Features

**Learning**
- 6 levels, 24 topics, 126 questions in 15 categories (single answer, multi-select, true/false, scenario).
- Practice with feedback after each answer; level exams (4 categories × 5 questions × 5 marks = 100).
- Pass a level to unlock the next one; badges; **PDF certificate** with QR code and a public verify page.
- Teachers assign exams, write practice questions and download class reports (CSV / PDF / certificate ZIP).

**Schools and business**
- Schools, classes, sections (35 students by default), CSV import with preview, family consent.
- Licence plans (Trial, Basic, Standard, Unlimited), Level Packs, product keys, 50% community discount.
- **Payments by bank transfer:** payslip upload → Super Admin approves → plan or pack switches on → PDF tax receipt
  with 15% GST. No card details are ever collected.
- **Business intelligence:** income per month, plan mix, exams per month, pass rates, weakest categories, tickets.

**Support and communication**
- **Tickets (Tautoko)** for every role: CQ-0001 numbers, routing, target times, state machine, internal notes,
  attachments, "Report this question".
- **Emails:** editable templates, Gmail SMTP when set up, email log, bulk email with preview and unsubscribe link,
  `poll_inbox` command that turns support emails into tickets with an automatic reply.
- **Announcements (Pānui)**, dashboard notices (Observer pattern).
- **Help centre** and an **"Explain this page"** button on every page, with a question box for the helper.

**AI and integrations**
- **Integrations page:** Google Gemini, DeepSeek, Claude, OpenAI, **Other AI** (any OpenAI-compatible service such as
  OpenRouter, Groq, Mistral or a local Ollama), Gmail, Google Maps, WhatsApp, Viber. Keys are encrypted, shown
  masked, tested with one button, and every change is in the security log.
- **AI models page** (Super Admin): switch each model on or off, choose the **default**, and set the **order**.
  The agreed order is Gemini, then DeepSeek, then Claude, OpenAI and Other AI. When a model fails – free tokens
  used up (429), no credit (402), wrong key, no internet – CyberQuest **switches to the next model automatically**,
  and the offline helper is always last. **Check** / **Check all models** ask each model one tiny question, so a green
  result means the key works *and* tokens are available.
- **WhatsApp test message** (Super Admin): send Meta's `hello_world` template to one number to prove the
  WhatsApp Cloud API really sends.
- **AI test page** and **AI drafts** (question, tip, parent message, explanation). Names and emails are removed before
  sending. Every draft needs a **teacher approval**, and Māori content also needs the **Cultural Guide (Kaiārahi)**.
- Works fully offline: without a key an offline helper makes simple drafts.
- **Media library:** images, audio, video, PDF (type checked by file signature, size limits), YouTube videos in
  privacy mode (youtube-nocookie.com).
- Free share buttons (WhatsApp, Viber, Facebook) and Google Maps on the school page.

**Security**
- Roles and permission decorators, login lockout (5 tries → 15 minutes), two-step login (TOTP) that the Super Admin
  can switch on or off per user, forgot password by email / WhatsApp / Viber (1-hour link, same message for every
  username, 3 requests per hour).
- Security log and audit log, Content Security Policy with no inline JavaScript, health check `/health/`,
  backups and restore, maintenance mode, feature switches, "are you sure?" screens before overwriting settings.

**Accessibility**
- Atkinson Hyperlegible font, keyboard focus, skip link, alt text, **dark mode** and **larger text** buttons.

---

## 4. Folder structure

```
cyberquest/            Django project: settings (base / dev / test / prod), urls, wsgi
apps/
  core/                settings singleton, audit log, health, backups, middleware, PDF fonts, seed_demo
  accounts/            User model, roles, login, MFA, Login as, password reset
  security/            security log and lockout
  schools/             schools, classes, sections, students, CSV import
  licensing/           plans, licences, Level Packs, product keys
  payments/            payslips, approval, receipts
  learning/            levels, topics, questions, question factory, content import
  quizzes/             practice and exams (strategy), scoring, progression, badges
  certificates/        PDF certificates, verify page, ZIP
  helpdesk/            tickets
  emails/              templates, sending, bulk, unsubscribe, poll_inbox
  notifications/       observer and dashboard notices
  announcements/       Pānui
  reports/             BI service, reports, CSV / PDF export
  helpcentre/          help articles, Explain this page
  integrations/        adapters and the encrypted key vault
  ai_assistant/        AI drafts and the page helper
  medialib/            uploads and YouTube
  website/             public website (home, features, pricing, about, contact)
templates/  static/    shared templates, CSS, JavaScript, local Bootstrap / Chart.js
data/                  learning content (JSON)
tests/                 pytest tests
docs/                  CONCEPTS.md, evidence screenshots and test results per student
docker/  Dockerfile  docker-compose.yml  run.bat  run_local.bat  run.sh
```

---

## 5. Tests and code quality

```bash
pip install -r requirements-dev.txt
python -m pytest                       # 113 tests
pylint apps cyberquest tests           # 10.00/10
coverage run -m pytest && coverage report    # 79% of apps/
black --check .                        # formatting
```

The test date is fixed to 6 October 2026 so licence tests give the same result every day. The latest results are in
`docs/evidence/Jihe_Qi/test_results/`.

---

## 6. OOP and design patterns

See **[docs/CONCEPTS.md](docs/CONCEPTS.md)** for where each concept is used: classes and objects, inheritance,
abstract classes, polymorphism, encapsulation, composition, Factory, Strategy, Observer, Singleton, Adapter,
Decorator, State machine, Repository (QuerySets) and custom exceptions.

---

## 7. Settings (.env)

| Variable | Meaning |
|---|---|
| `DJANGO_SECRET_KEY` | Secret key (run.bat makes a random one) |
| `FIELD_ENCRYPTION_KEY` | Key for the encrypted API key vault (made from the secret key if empty) |
| `DEMO_MODE` | `1` shows the demo accounts page and demo buttons |
| `HOST_PORT` | Port on your computer (run.bat sets a free one) |
| `DATABASE_ENGINE` | `sqlite` (default) or `postgres` |

API keys for AI, Gmail, Maps, WhatsApp and Viber are **not** in `.env`. The Super Admin adds them on the
Integrations page, where they are stored encrypted. Never commit `.env`.

---

## 8. Licence of third-party files

Bootstrap, Bootstrap Icons and Chart.js (MIT) and the Atkinson Hyperlegible font (SIL Open Font Licence) are included
locally so the app works without internet. Their licence files are next to them in `static/vendor/` and
`apps/core/fonts/`.
