# CyberQuest (Django)

**Learn. Play. Decide. Stay Cyber Safe.**

CyberQuest is a cyber-safety learning platform for New Zealand schools. Students study short topics, practise with instant feedback, sit level exams and earn certificates. Teachers assign exams and read class reports. School Admins run classes, students and the licence. The Super Admin runs the whole platform.

This version is the Django rebuild of the team's earlier Flask prototype, made for **MSE800 Professional Software Engineering – Assessment 2** at Yoobee College of Creative Innovation (lecturer: Dr. Farah Younas).

|                   |                                                    |
| ----------------- | -------------------------------------------------- |
| Project code      | ``                                                  |
| Simulated company | Mount Everest Digital Limited                      |
| Version           | 2.0.0                                              |
| Repository        | https://github.com/anishnz/Django_CyberSecurity_YB |

> **Simulation note.** The company, client, schools, students, payments and Māori advisers in the demo data are made up for this college project. No real student data is used. Demo bank numbers and payslips are marked "demo".

---

## 1. Team

| Student        | ID        | Role in the team                                 | Main parts of the code                                                                                  |
| -------------- | --------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| Anish Shrestha | 270889991 | Lead Software Engineer, system designer          | accounts, roles, security, Login as, MFA, password reset, AI drafts, settings, Docker and run scripts   |
| Rajneesh Kumar | 270245010 | Backend and database developer                   | schools, licensing, payments, help desk rules, emails, announcements, notifications                     |
| Dinesh Upreti  | 270830269 | Frontend developer and business analyst          | public website, student and teacher screens, reports and BI, certificates, help centre, display options |
| Jihe Qi        | 271008116 | Product Manager, integrations, meeting secretary | requirements analyst, integrations vault, AI test page, media library, upload checks, demo data         |

Every member also wrote code in the other areas and reviewed each other's pull requests (see the Git history: `feature/<name>-<feature>` branches merged into `develop`).

---

## 2. Run it

### Windows – one double-click (Docker)

1. Install **Docker Desktop** and start it.
2. Double-click **`run.bat`**. It:
   - checks Docker is running,
   - finds a **free port** (8000, or the next free port up to 8020) so it never clashes with another program,
   - creates `.env` with random secrets on the first run,
   - starts the container, waits for `/health/`, and opens your browser.
3. Stop it with `docker compose down`.

### Windows without Docker

Double-click **`run_local.bat`** (needs Python 3.10 or newer). It makes a virtual environment, installs the packages, prepares the database, loads the demo data and starts the **waitress** server on a free port.

### Mac / Linux

```bash
./run.sh                 # Docker, same free-port check
# or by hand:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate && python manage.py seed_demo
python manage.py runserver
```

> **Knowledge Base note.** `run.bat`, `run_local.bat` and `run.sh` start **only the website**. The **Knowledge Base** tab also needs the RAG service and an AI model server running. Everything else works without them. See section 9 and the step-by-step guide in section 10.

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

The Super Admin can also use **Login as** to open any dashboard. A red bar shows who you are viewing as, and every Login as is written to the security log.

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
- **Payments by bank transfer:** payslip upload → Super Admin approves → plan or pack switches on → PDF tax receipt with 15% GST. No card details are ever collected.
- **Business intelligence:** income per month, plan mix, exams per month, pass rates, weakest categories, tickets.

**Support and communication**
- **Tickets (Tautoko)** for every role: CQ-0001 numbers, routing, target times, state machine, internal notes, attachments, "Report this question".
- **Emails:** editable templates, Gmail SMTP when set up, email log, bulk email with preview and unsubscribe link, `poll_inbox` command that turns support emails into tickets with an automatic reply.
- **Announcements (Pānui)**, dashboard notices (Observer pattern).
- **Help centre** and an **"Explain this page"** button on every page, with a question box for the helper.

**AI and integrations**
- **Integrations page:** Claude, OpenAI, Gemini, Gmail, Google Maps, WhatsApp, Viber. Keys are encrypted, shown masked, tested with one button, and every change is in the security log.
- **AI test page** and **AI drafts** (question, tip, parent message, explanation). Names and emails are removed before sending. Every draft needs a **teacher approval**, and Māori content also needs the **Cultural Guide (Kaiārahi)**.
- Works fully offline: without a key an offline helper makes simple drafts.
- **Media library:** images, audio, video, PDF (type checked by file signature, size limits), YouTube videos in privacy mode (youtube-nocookie.com).
- Free share buttons (WhatsApp, Viber, Facebook) and Google Maps on the school page.
- **Knowledge Base (RAG):** a **Knowledge Base** tab where everyone can ask questions and get answers with sources.
  Staff upload documents; teachers and admins generate quiz questions; the Super Admin sets the AI model. One shared Knowledge Base for all schools. Needs the extra RAG service (see [section 9](#9-knowledge-base-rag)).

**Security**
- Roles and permission decorators, login lockout (5 tries → 15 minutes), two-step login (TOTP) that the Super Admin can switch on or off per user, forgot password by email / WhatsApp / Viber (1-hour link, same message for every username, 3 requests per hour).
- Security log and audit log, Content Security Policy with no inline JavaScript, health check `/health/`, backups and restore, maintenance mode, feature switches, "are you sure?" screens before overwriting settings.

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
  kb/                  Knowledge Base pages and the proxy to the RAG service
templates/  static/    shared templates, CSS, JavaScript, local Bootstrap / Chart.js
data/                  learning content (JSON)
tests/                 pytest tests
docs/                  CONCEPTS.md, evidence screenshots and test results per student
cyberquest-rag/        Knowledge Base (RAG) service: FastAPI app, vector store, sample knowledge document
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

The test date is fixed to 6 October 2026 so licence tests give the same result every day. The latest results are in `docs/evidence/Jihe_Qi/test_results/`.

---

## 6. OOP and design patterns

See **[docs/CONCEPTS.md](docs/CONCEPTS.md)** for where each concept is used: classes and objects, inheritance,
abstract classes, polymorphism, encapsulation, composition, Factory, Strategy, Observer, Singleton, Adapter, Decorator, State machine, Repository (QuerySets) and custom exceptions.

---

## 7. Settings (.env)

| Variable | Meaning |
|---|---|
| `DJANGO_SECRET_KEY` | Secret key (run.bat makes a random one) |
| `FIELD_ENCRYPTION_KEY` | Key for the encrypted API key vault (made from the secret key if empty) |
| `DEMO_MODE` | `1` shows the demo accounts page and demo buttons |
| `HOST_PORT` | Port on your computer (run.bat sets a free one) |
| `DATABASE_ENGINE` | `sqlite` (default) or `postgres` |
| `RAG_BASE_URL` | Address of the Knowledge Base (RAG) service, default `http://127.0.0.1:9000` (see [section 9](#9-knowledge-base-rag)) |
| `RAG_SERVICE_KEY` | Shared secret between CyberQuest and the RAG service; must be identical on both sides |

API keys for AI, Gmail, Maps, WhatsApp and Viber are **not** in `.env`. The Super Admin adds them on the Integrations page, where they are stored encrypted. Never commit `.env`. (The AI model of the Knowledge Base is different: it is set on the **Manage Knowledge Base** page and stored by the RAG service, not by Django.)

---

## 8. Licence of third-party files

Bootstrap, Bootstrap Icons and Chart.js (MIT) and the Atkinson Hyperlegible font (SIL Open Font Licence) are included locally so the app works without internet. Their licence files are next to them in `static/vendor/` and
`apps/core/fonts/`.

---

## 9. Knowledge Base (RAG)

### 9.1 What it is

The **Knowledge Base (KB)** is a question-and-answer helper. Staff upload documents (for example the cyber-safety course notes). Anyone who is signed in can then type a question, for example *"What is phishing?"*, and get a short answer **with the sources** it came from. Teachers and admins can also ask it to write **multiple-choice quiz questions**
from the same documents.

It is a **RAG** feature (*retrieval-augmented generation*): first the service **finds** the most fitting pieces of the uploaded documents, then an AI model **writes the answer using only those pieces**. This keeps answers tied to the school's own material. The AI can still make mistakes, and the page says so.

There is **one shared Knowledge Base for all schools**. Nothing in `apps/kb` is filtered by school, and the module has no database tables of its own.

### 9.2 How it works (architecture)

Three programs work together. Only the first one is started by `run.bat`, `run_local.bat` or `run.sh`.

```
 Browser (student, teacher, admin ...)
    |  HTTP, same site: /kb/ pages and /kb/api/... (JSON)
    v
 CyberQuest Django site            port 8000   <- apps/kb is a thin proxy
    |  HTTP + headers X-Service-Key and X-User-Role   (RAG_BASE_URL)
    v
 RAG service (FastAPI + uvicorn)   port 9000   <- folder cyberquest-rag/
    |  finds the best text pieces in its own vector store (Chroma, folder cyberquest-rag/data/)
    |  OpenAI-compatible "Chat Completions" call   (base URL saved in the model settings)
    v
 AI model server (DeepSeek, model id deepseek-v4-flash-0731)   <deepseek-host>:<port>
```

Request flow for one question:

1. The user types a question on the **Knowledge Base** page. The page sends it to `/kb/api/ask/` (same site, so the browser never talks to the RAG service or the model directly).
2. `apps/kb/api.py` checks the user is signed in and allowed, checks the question (1 to 1000 characters), and works out the user's **role** (`role_of()` in `apps/kb/services.py`).
3. `apps/kb/services.py` calls the RAG service at `RAG_BASE_URL` with two headers: `X-Service-Key` (the shared secret `RAG_SERVICE_KEY`) and X-User-Role (student, teacher or super_admin).
4. The RAG service checks the key and the role again, searches its vector store, builds a prompt from the best text pieces and sends it to the AI model.
5. The answer and its sources go back the same way and the page shows them.

Role mapping sent to the RAG service (`role_of()`): Super Admin → `super_admin`; Teacher and School Admin → `teacher`;
Student and Guest → `student`. The RAG service only knows these three roles, so the rule *"school admins may delete, teachers may not"* is enforced **in Django** (`apps/kb/api.py`).

### 9.3 Where it appears in the app

- A **Knowledge Base** tab (book icon) in the top navigation for **every signed-in role**, including the Demo Guest  (KB_MENU_ITEM in apps/accounts/roles.py). Super Admin sees it just before System; the other roles see it as the last tab. Visitors who are not signed in do not see it.
- **Ask page** – `/kb/` (page title *Knowledge Base*). Question box, **Ask** button, answer and sources. Staff also see a **Manage Knowledge Base** button.
- **Manage page** – `/kb/manage/` (page title *Manage Knowledge Base*). For Teacher, School Admin and Super Admin only. It  has an **Ask a question** button back to the Ask page.

Not signed in? Both pages send you to the login page.

### 9.4 Features

**Asking questions (Ask page, everyone).**
Type a question (up to 1000 characters) and press **Ask** (or press `Ctrl` + `Enter` in the box). While the service works you see Thinking.... The answer is shown in an Answer card. Below it a Sources card lists each source as [1] Title with the first part of the matching text. The answer cites sources as [1], [2] and so on. Up to 5 text pieces are used. If nothing fits, the answer is "I couldn't find this in the knowledge base." (English only) and "No sources were used for this answer." is shown. For students and guests the AI is told to keep answers short and age-appropriate. The AI is also told never to explain how to attack or harm real systems or people.

**Uploading documents (Manage page, Teacher / School Admin / Super Admin).**
- Allowed file types: **PDF, TXT, Markdown (`.md`)**. Maximum size: **20 MB**. Anything else is refused.
- Fields: **File** (the **Choose file** button), **Title** (optional, up to 120 characters, shown as the source name in answers; if empty the file name is used) and **Tags** (optional, up to 120 characters, for example `courses, fees`).
- The service reads the text, splits it into pieces of about 800 characters, turns each piece into numbers (an *embedding*) and stores them. After a successful upload the page says *"Uploaded. The document was split into N chunks."* and refreshes the list.
- Plain text and Markdown work best. PDFs are read as text only: tables are often read badly, and a scanned PDF (a picture of text) has no readable text and is refused with *"No readable text found in the document"*.
- Uploading the same file twice creates **two** documents (there is no duplicate check).
- Every upload is written to the audit log (`kb_document_uploaded`).

**Listing documents (Manage page, Teacher / School Admin / Super Admin).**
The **Documents** table shows **Title**, **Tags** and **Chunks** (how many text pieces the document was split into).

**Deleting documents (Manage page, School Admin / Super Admin only).**
Each row has a **Delete** button, only for these two roles; teachers do not see it. A confirmation box asks first, and deleting cannot be undone. The audit log gets `kb_document_deleted`.

**Generating quiz questions (Manage page, Teacher / School Admin / Super Admin).**
Enter a **Topic** (up to 300 characters), **Questions** (1 to 20, default 5) and **Difficulty** (Easy, Medium, Hard) and press **Generate**. This can take up to a minute. The AI writes multiple-choice questions (options A to D) from the best matching documents. Each question has a **Show answer** fold-out with the correct letter and an explanation, *based on:* line names the documents used. If the AI does not answer in the expected format, the page shows a warning and its raw answer; press **Generate** again. If the Knowledge Base has no matching material, you are told to upload some first.
The questions are only **shown on the page**: they are not saved into the CyberQuest question bank. Always read them before using them in class.

**AI model settings and connection test (Manage page, Super Admin only).**
The **AI model settings** card (marked *Super Admin*) is not even present in the page for other roles. Fields: **Display name**, API base URL, Model ID, API key (shown only masked as Current key: ***xxxx; leave it empty to keep the current key), **Temperature, Max tokens and Timeout (seconds). Save settings applies the change to the next question at once; there is no restart. Test connection asks the model to reply "pong" and shows "Connection works. The model replied: ..." or the error. These settings are stored by the RAG service in cyberquest-rag/data/model_config.json, not in Django. Saving is written to the audit log as kb_model_settings_changed (field names only, never the key).

**Other things you can rely on.**
- Everything the AI or the server sends is inserted into the page as plain text, never as HTML.
- A refused action (wrong role) is written to the security log as `access_denied`.
- The RAG service also has a lesson-plan endpoint (`/v1/lesson-plan`) and a `/v1/model-info` endpoint, but **Django does not use them and no page offers them**.

### 9.5 Who can do what

Derived from `apps/kb/api.py` (`kb_api(...)` role lists), `apps/kb/views.py` (`role_required`), `role_of()` and the templates. ✔ = allowed, ✘ = refused.

| Action | Guest | Student | Teacher | School Admin | Super Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| See the **Knowledge Base** tab and open the Ask page | ✔ | ✔ | ✔ | ✔ | ✔ |
| Ask a question (answer + sources) | ✔ | ✔ | ✔ | ✔ | ✔ |
| Open the Manage page | ✘ | ✘ | ✔ | ✔ | ✔ |
| List documents | ✘ | ✘ | ✔ | ✔ | ✔ |
| Upload a document | ✘ | ✘ | ✔ | ✔ | ✔ |
| Generate quiz questions | ✘ | ✘ | ✔ | ✔ | ✔ |
| Delete a document | ✘ | ✘ | ✘ | ✔ | ✔ |
| View / change AI model settings, Test connection | ✘ | ✘ | ✘ | ✘ | ✔ |

Notes:
- Guests can ask even though the Demo Guest is otherwise read-only:  `apps/accounts/middleware.py` lets POST requests to `/kb/api/` through so the KB can answer guests itself (and refuse them with a JSON 403 on every staff endpoint).
- Students sign in only when family consent is recorded (existing rule, not specific to the KB).
- The delete rule (School Admin and Super Admin only) is checked in Django. The RAG service itself treats School Admins   and Teachers alike, so it never receives a delete request from a teacher through CyberQuest.

### 9.6 Endpoints

Pages and JSON endpoints of the Django site (`apps/kb/urls.py`, mounted at `kb/` in `cyberquest/urls.py`). The JSON endpoints answer errors as `{"detail": "<English message>"}`, with status 401 when not signed in. They need the normal Django CSRF token (the pages send it) and are not meant to be called by other programs.

| Method | Path | Allowed roles | Purpose |
|---|---|---|---|
| GET | `/kb/` | all signed-in roles | Ask page |
| GET | `/kb/manage/` | Teacher, School Admin, Super Admin | Manage page |
| POST | `/kb/api/ask/` | all signed-in roles | Ask a question → `answer` + `sources` |
| POST | `/kb/api/quiz/` | Teacher, School Admin, Super Admin | Generate quiz questions (`topic`, `count` 1-20, `difficulty` easy / medium / hard) |
| GET | `/kb/api/documents/` | Teacher, School Admin, Super Admin | List documents |
| POST | `/kb/api/documents/` | Teacher, School Admin, Super Admin | Upload a document (`file`, optional `title`, `tags`) |
| DELETE | `/kb/api/documents/<doc_id>/` | School Admin, Super Admin | Delete a document (`doc_id`: letters, digits, `_`, `-`, up to 64 characters) |
| GET | `/kb/api/admin/model/` | Super Admin | Read the AI model settings (key masked) |
| PUT | `/kb/api/admin/model/` | Super Admin | Change the AI model settings (empty fields keep the current value) |
| POST | `/kb/api/admin/model/test/` | Super Admin | Check that the AI model answers |

> **Note.** The base path is `/kb/` (pages) and `/kb/api/` (JSON). Earlier notes and the example file `cyberquest-rag/django_side/kb_api.py` mention `/api/kb/`; that is **not** what this project uses.

What the Django proxy calls on the RAG service (each needs the `X-Service-Key` header):

| RAG service path | Used for | Roles it accepts |
|---|---|---|
| `GET /health` (no key needed) | Is the service alive? Returns `{"ok": true}` | any |
| `POST /v1/ask` | Ask | student, teacher, super_admin |
| `POST /v1/quiz` | Quiz questions | teacher, super_admin |
| `GET` / `POST /v1/documents` | List / upload | teacher, super_admin |
| `DELETE /v1/documents/<doc_id>` | Delete | teacher, super_admin |
| `GET` / `PUT /v1/admin/model` | Read / change model settings | super_admin |
| `POST /v1/admin/model/test` | Connection test | super_admin |
| `POST /v1/lesson-plan`, `GET /v1/model-info` | Exist in the service, **not used** by Django | – |

### 9.7 Configuration

**CyberQuest (Django) – in `.env`, read by `cyberquest/settings/base.py` through `env()`:**

| Name | Default | What it does |
|---|---|---|
| `RAG_BASE_URL` | `http://127.0.0.1:9000` | Where Django finds the RAG service. Used by `apps/kb/services.py`. |
| `RAG_SERVICE_KEY` | empty | The shared secret sent as `X-Service-Key`. Must be **exactly the same** as `RAG_SERVICE_KEY` of the RAG service. |

Django reads `.env` once when it starts: after changing it, restart the site. Fixed values in `apps/kb/services.py`: wait up to **5 seconds** to reach the service and up to **180 seconds** for its answer. Upload limit (20 MB), question limit (1000 characters) and file types are fixed in `apps/kb/api.py`.

**RAG service – environment variables read by `cyberquest-rag/app/config.py` (example file: `cyberquest-rag/.env.example`):**

| Name              | Default                                 | What it does                                                                                                              |
| ----------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `RAG_SERVICE_KEY` | none – **required**                     | The shared secret. The service refuses to start without it.                                                               |
| `RAG_DATA_DIR`    | `./data`                                | Folder for the vector store (`chroma/`) and `model_config.json`. It is relative to the folder you start the service from. |
| `RAG_EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | The model that turns text into numbers for searching. Downloaded once from Hugging Face on first start.                   |
| `RAG_MIN_SCORE`   | `0.2`                                   | Text pieces that match worse than this are ignored.                                                                       |


> The RAG service code does **not** read the `.env` file by itself (there is no `.env` loader in `cyberquest-rag/app/`).
> Set the variables in the terminal or in the PyCharm run configuration. See [section 10.3](#103-component-2-the-rag-service).

**AI model settings** (display name, API base URL, model ID, API key, temperature, max tokens, timeout) are **not** environment variables. They live in `cyberquest-rag/data/model_config.json`, are created with built-in defaults on the first start, and are changed by the Super Admin on the Manage page. Built-in defaults: model ID deepseek-v4-flash-0731, API key EMPTY, temperature 0.3, max tokens 1500, timeout 120 seconds. The default API base URL in the code points to a developer machine, so set your own (`http://<deepseek-host>:<port>/v1`). Never write real keys into the README or Git.

### 9.8 What users see when something is not working

| Situation | Message on the page |
|---|---|
| RAG service not running, wrong address, too slow, or not answering with JSON | *The knowledge base service is not running right now. Please try again later.* |
| Service key differs between Django and the RAG service | *The knowledge base service refused the connection. Ask the Super Admin to check the service key.* |
| AI model unreachable or failing | Normal users: *The AI model did not answer. Please try again in a moment.* The **Super Admin** sees the technical reason instead (for example `Model call failed: ...`). |
| Not signed in any more | *Please sign in again.* |
| Role not allowed | *You do not have permission to do this.* (the Manage page shows the normal "No access" page) |
| Empty or too long question / topic, bad number of questions | A short *Please ...* or *... too long ...* message; nothing is sent to the service. |
| Nothing found for a question | *I couldn't find this in the knowledge base.* |
| Quiz topic has no matching documents | *No relevant material in the knowledge base; upload some first* |
| Wrong file type, file over 20 MB, no readable text | *Only PDF, TXT and Markdown (.md) files can be uploaded.* / *That file is too large (20 MB maximum).* / *No readable text found in the document* |

Django also writes a line such as `KB service request failed: POST /v1/ask (ConnectionError)` to the console and to `logs/cyberquest.log`. The step-by-step fixes are in [section 10.8](#108-troubleshooting).

### 9.9 Where the code lives

| Path | What |
|---|---|
| `apps/kb/urls.py`, `views.py` | The two pages and the URL map |
| `apps/kb/api.py` | JSON endpoints, role checks, input checks, audit entries |
| `apps/kb/services.py` | The only code that calls the RAG service (`call_rag`, `role_of`) |
| `apps/kb/templates/kb/ask.html`, `manage.html` | The pages |
| `static/js/kb_common.js`, `kb_ask.js`, `kb_manage.js` | Page scripts (no inline JavaScript, because of the Content Security Policy) |
| `apps/accounts/roles.py` | The **Knowledge Base** tab (`KB_MENU_ITEM`) |
| `tests/test_kb_api.py`, `test_kb_pages.py`, `kb_support.py` | KB tests. The RAG service is always faked, so they run without it. |
| `cyberquest-rag/app/` | RAG service: `main.py` (endpoints), `store.py` (read, split, store, search), `llm.py` (model call), `config.py` (settings) |
| `cyberquest-rag/cybersecurity_knowledge_base_L0-L6_English.md` | Sample knowledge document (levels L0 to L6) to upload first |

---

## 10. Running everything (step by step)

This guide is for a complete beginner on **Windows**. Do the steps in order and do not skip the "You should see" lines: they tell you whether a step worked. Commands go into a **terminal**; each block says which one.

> Sections 2 and 7 above explain the quick way to start **only the website**. This section explains how to start the **whole system** that the Knowledge Base needs. Without the RAG service and the AI model, the rest of CyberQuest still works; only the **Knowledge Base** tab shows *"The knowledge base service is not running right now."*

### 10.1 The three parts and the start order

| #   | Part                                | What it does                                                                            | Runs on                        | Port                                                                                   | Folder            |
| --- | ----------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------- | ----------------- |
| 1   | **RAG service** (FastAPI + uvicorn) | Stores the uploaded documents, finds the best pieces for a question, asks the AI model. | The developer's **Windows PC** | `9000`                                                                                 | `cyberquest-rag/` |
| 2   | **CyberQuest website** (Django)     | The pages people use. Its `apps/kb` app talks to the RAG service.                       | The developer's **Windows PC** | `8000` (PyCharm) or the first free port from 8000 to 8020 (`run.bat`, `run_local.bat`) | project root      |


**Start order: 1 → 2 → . Stop order:  2 → 1** (the model server is usually left running by its owner).
Why this order: each part depends on the one before it (the website calls the RAG service, and the RAG service calls the AI model). Starting and checking them in this order shows you exactly where a problem is.

Where each part is configured:

```
AI model address, model id, key  ->  Manage Knowledge Base page (Super Admin)  ->  cyberquest-rag/data/model_config.json
RAG service key and data folder  ->  environment variables of the RAG service (section 9.7)
Where the website finds the RAG  ->  RAG_BASE_URL and RAG_SERVICE_KEY in the website's .env
```

### 10.2 Component 1: the AI model server (DeepSeek)

**What you need to know.** CyberQuest does not contain the AI model. The RAG service sends questions to an AI model server that offers an OpenAI-compatible Chat Completions API (the code uses the openai Python package with a base URL, see cyberquest-rag/app/llm.py). The model id the project expects is deepseek-v4-flash-0731. This server runs on another machine, so you normally do not start it on your own PC: you only need to know its address.

**What to ask the owner of the model machine for:**

1. The address in the form `http://<deepseek-host>:<port>/v1` (this is the **API base URL**).
2. The model id: `deepseek-v4-flash-0731`.
3. An API key if the server checks one. If it does not, the RAG service uses the placeholder `EMPTY`.

**How to check it works.**

- Easiest and verified: sign in as **Super Admin**, open **Knowledge Base → Manage Knowledge Base**, fill in **AI model settings** (section 10.6, step 3) and press **Test connection**. You should see *"Connection works. The model replied: ..."*.

You should see some JSON that contains the model id. A "could not connect" error means the model server is off, the address or port is wrong, or your PC cannot reach that machine (network or VPN).

**Stop / restart / change the port.** Done on the model machine by its owner (see the TODO above). If the address or port changes, you only need to update **API base URL** on the Manage page: the RAG service reads the settings again on every question, so **no restart** is needed.

### 10.3 Component 2: the RAG service

The RAG service lives in the folder `cyberquest-rag/` of this project. It has its **own** Python packages, so it gets its **own virtual environment** (a private folder of Python packages, here `cyberquest-rag/.venv`).

#### One-time setup – the command line way

1. Open **Command Prompt** or **PowerShell** (Windows key, type `cmd` or `powershell`, Enter) and go to the folder (use your own path):

```powershell
cd G:\Django_CyberSecurity_YB\cyberquest-rag
```

   You should see the folder path in front of the cursor.

2. Create the virtual environment (once):

```powershell
python -m venv .venv
```

   Nothing is printed; a `.venv` folder appears inside `cyberquest-rag`.

3. Activate it (**every time you open a new terminal**):

   PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

   Command Prompt:

```bat
.venv\Scripts\activate.bat
```

   You should see `(.venv)` at the start of the line. *Why:* it makes `python` and `pip` use the private packages.
   If PowerShell says that running scripts is disabled, use Command Prompt instead.

#### Install the packages (once)

In the terminal, with `(.venv)` showing and inside `cyberquest-rag`:

```powershell
python -m pip install -r requirements.txt
```

You should see a long list ending with *Successfully installed ...*. This takes a few minutes.

#### Configure it (once)

The RAG service needs the variable **`RAG_SERVICE_KEY`**; it **refuses to start without it** (`RuntimeError: RAG_SERVICE_KEY is not set`). It does not read a `.env` file itself, so give it the variables in the terminal or in the PyCharm run configuration. The names are the ones in `cyberquest-rag/.env.example`:

| Variable | Value |
|---|---|
| `RAG_SERVICE_KEY` | A long random secret. **The same value** must be put in the website's `.env` as `RAG_SERVICE_KEY`. |
| `RAG_DATA_DIR` | Optional. Default `./data` (relative to the folder you start from). |
| `RAG_EMBED_MODEL`, `RAG_MIN_SCORE` | Optional, see section 9.7. |

To make a random secret (any terminal where Python works):

```powershell
python -c "import secrets;print(secrets.token_urlsafe(32))"
```

This prints one line of random letters. Copy it. **Never** commit it or paste it into the README.

#### Start it – command line

In a terminal in `cyberquest-rag` with `(.venv)` showing (it works the same in the PyCharm **Terminal**). PowerShell:

```powershell
$env:RAG_SERVICE_KEY = "your-key-here"
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

Command Prompt:

```bat
set RAG_SERVICE_KEY=your-key-here
python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
```

*Why `--host 127.0.0.1`:* only programs on your own PC can reach it. *Why this folder:* `app.main` is found relative to it, and so is `./data`. The variable lasts only for that terminal window.
You should see `Uvicorn running on http://127.0.0.1:9000`. **Leave this window open.**

#### Check that it works

Open this address in a browser (or run the `curl` line in a **second** terminal):

```text
http://127.0.0.1:9000/health
```

```powershell
curl.exe http://127.0.0.1:9000/health
```

You should see `{"ok":true}`. This address needs no key. (FastAPI's automatic page `http://127.0.0.1:9000/docs` also lists the endpoints.) Until the website is started and **Test connection** works, you have only proven that the service is alive, not that it can reach the AI model.

#### Stop, restart, change the port

- **Stop:** PyCharm: the red **Stop** square in the Run panel. Terminal: click in the window and press `Ctrl` + `C`.
- **Restart:** start it again the same way. The uploaded documents stay (they are saved in `cyberquest-rag/data/chroma/`).
- **Change the port:** change `--port 9000` **and** change `RAG_BASE_URL` in the website's `.env` to the same port, then restart both.
- **Port already in use** (error such as `[WinError 10048]`): see section 10.8.

### 10.4 Component 3: the CyberQuest website (Django)

#### Prerequisites

- Windows PC with **Python 3.10 or newer** (`run_local.bat` checks this). Install it from https://www.python.org/downloads/ and tick **"Add to PATH"**.
- PyCharm is optional but recommended. Docker Desktop is needed **only** for the Docker way (`run.bat`).

#### One-time setup – the command line way

Open **Command Prompt** or **PowerShell** in the **project root** (use your own path) and run:

```powershell
cd G:\Django_CyberSecurity_YB
python -m venv .venv
.venv\Scripts\Activate.ps1
```

(Command Prompt: use `.venv\Scripts\activate.bat` for the last line.) You should see `(.venv)` in front of the cursor.
Then, in the same window (also the PyCharm **Terminal**):

```powershell
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py seed_demo
```

You should see the packages install, then a list of `OK` migrations, then the demo data loading. These commands come from section 2 above. `requirements.txt` alone is enough to run the site; `requirements-dev.txt` also adds the test tools.

#### Configure it (once)

Create a file named `.env` in the project root by copying `.env.example` (if you ever used `run.bat` or `run_local.bat`, it already exists). The two Knowledge Base lines are:

```text
RAG_BASE_URL=http://127.0.0.1:9000
RAG_SERVICE_KEY=your-key-here
```

Put the **same** secret that you gave the RAG service. `.env.example` ships with the placeholder `change-me`: **replace it**, and replace it on both sides, or the Knowledge Base says *"...refused the connection. Ask the Super Admin to check the service key."* Other `.env` names are in section 7. Restart the website after every `.env` change.

`manage.py` uses `cyberquest.settings.dev` (debug on, SQLite) unless a real environment variable `DJANGO_SETTINGS_MODULE` is already set; the `DJANGO_SETTINGS_MODULE` line inside `.env` is read too late to change that.
Docker and `run_local.bat` set `cyberquest.settings.prod` themselves. For PyCharm on your PC, `dev` is the expected setting.

#### Start it – way 1: `run_local.bat` (no Docker)

Double-click **`run_local.bat`** in the project folder. It creates `.venv`, installs `requirements.txt`, prepares the database, loads the demo data, **picks the first free port from 8000 to 8020**, opens your browser and runs the **waitress** server.
Read the port it prints (`CyberQuest is running at http://127.0.0.1:<port>/`). Stop it with `Ctrl` + `C`.

#### Start it – way 2: `run.bat` (Docker)

1. Start **Docker Desktop** and wait until it says it is running.
2. Double-click **`run.bat`** (details in section 2). It picks a free port from 8000 to 8020, creates `.env` on the first run, starts the container, waits for `/health/` and opens your browser.
3. Stop it with `docker compose down` (in a terminal in the project root). See the logs with `docker compose logs web`.

On Mac / Linux, `./run.sh` does the same thing as `run.bat` (verified in the script).

> **Docker and the Knowledge Base.** Inside the Docker container, `127.0.0.1` means *the container itself*, not your PC.
> `RAG_BASE_URL=http://127.0.0.1:9000` therefore does **not** reach a RAG service that runs on your PC. The repository does not contain a Docker setup for the RAG service or a setting that connects the container to it.
>
> **TODO (maintainer to confirm):** how the Docker-run website should reach the RAG service on the host PC (the value of `RAG_BASE_URL` and whether the RAG service must listen on more than `127.0.0.1`). For the Knowledge Base, the PyCharm / `runserver` way (way 1 or 2) is the way that matches the documented setup.

#### Check that it works

Open in a browser (use the port from your start method):

```text
http://localhost:8000/health/
```

You should see JSON containing `"status": "ok"`. Then open `http://localhost:8000/`: the CyberQuest home page. Log in with a demo account from section 2 (**Demo logins**). After signing in you should see a **Knowledge Base** tab in the top menu.

#### Stop, restart, change the port

- **Stop:** PyCharm: red **Stop** square. Terminal: `Ctrl` + `C`. Docker: `docker compose down`.
- **Restart:** start it the same way again. Your data stays in `instance/cyberquest.sqlite3`. (Docker keeps its own data in Docker volumes.)
- **Change the port:** with `runserver`, write another number, e.g. `python manage.py runserver 8010`. `.env.example` lists `DJANGO_CSRF_TRUSTED_ORIGINS` for port 8000 only. If forms show a "403" page on another port, add the new address there (for
  example `http://localhost:8010,http://127.0.0.1:8010`) and restart. With `run.bat` / `run_local.bat` the port and this setting are chosen for you.

### 10.5 Cold start checklist (everything was closed or the PC was rebooted)

Tick each box only when its **check-point** shows what is written. If a check-point fails, stop and go to section 10.8.

- [ ] **1.  Open a terminal for the RAG service.** PyCharm: **Terminal** tab, or press the **Run** triangle of `RAG service` (then skip to step 4). Command line:

  ```powershell
  cd G:\Django_CyberSecurity_YB\cyberquest-rag
  .venv\Scripts\Activate.ps1
  ```

  *Check-point:* `(.venv)` is shown and the folder ends with `cyberquest-rag`.
- [ ] **2. Set the key and start the RAG service:**

  ```powershell
  $env:RAG_SERVICE_KEY = "your-key-here"
  python -m uvicorn app.main:app --host 127.0.0.1 --port 9000
  ```

  *Check-point:* the window says `Uvicorn running on http://127.0.0.1:9000`. Leave it open.
- [ ] **3. Check the RAG service.** Open `http://127.0.0.1:9000/health` in a browser. *Check-point:* `{"ok":true}`.
- [ ] **4. Open a second terminal in the project root and start the website:**

  ```powershell
  cd G:\Django_CyberSecurity_YB
  .venv\Scripts\Activate.ps1
  python manage.py runserver 8000
  ```

  (or press the green **Run** triangle of `CyberQuest` in PyCharm). *Check-point:* `Starting development server at http://127.0.0.1:8000/`.
- [ ] **5. Check the website.** Open `http://localhost:8000/health/`. *Check-point:* JSON with `"status": "ok"`.
- [ ] **6. Sign in as Super Admin** (`superadmin`, password in section 2 → **Demo logins**) at
  `http://localhost:8000/accounts/login/`. *Check-point:* you land on the Super Admin dashboard and see a **Knowledge Base** tab.
- [ ] **8. Check the whole chain.** **Knowledge Base → Manage Knowledge Base → AI model settings → Test connection.**
  *Check-point:* green message *"Connection works. The model replied: ..."*. This proves browser → website → RAG service → AI model all work.
- [ ] **9. Ask a test question.** On the **Knowledge Base** page type `What is phishing?` and press **Ask**.
  *Check-point:* an **Answer** and a **Sources** list appear (if documents were uploaded; if not, see section 10.6 first).

### 10.6 First-time Knowledge Base data setup

Do this once, after the whole system runs (section 10.5, steps 1 to 8). The vector store starts empty on a new computer.
(The `cyberquest-rag/data/` folder on a machine that was used before may already contain documents: open the Manage page and look at the **Documents** table first.)

1. Sign in as Super Admin (or any Teacher or School Admin; students and guests cannot upload).
2. Click the **Knowledge Base** tab, then **Manage Knowledge Base**. *You should see:* the **Upload a document** card and a **Documents** table that says *"No documents yet. Upload one above."* (or lists existing documents).
3. *(Super Admin, once)* In **AI model settings**, check **Display name**, **API base URL** (`http://<deepseek-host>:<port>/v1`), Model ID** (deepseek-v4-flash-0731) and API key (leave empty to keep EMPTY, or type the key if the server needs one). Press Save settings ("Model settings saved."), then Test connection.
4. In **Upload a document** press **Choose file** and select the sample document that ships with the project:
   ```text
   cyberquest-rag\cybersecurity_knowledge_base_L0-L6_English.md
   ```

5. Type a **Title**, for example `Cybersecurity Knowledge Base L0-L6` (this name is shown as the source of answers). **Tags** are optional.
6. Press **Upload**. *You should see:* *Reading and indexing...* (the first upload can take longer because the search model  loaded), then *"Uploaded. The document was split into N chunks."* and a new row in **Documents**.
7. Go to **Ask a question**. Type `What is phishing?` and press **Ask**. *You should see:* *Thinking...*, then an **Answer** that cites [1], [2] ... and a Sources list with the document title and a text snippet.
8. *(Teacher, School Admin or Super Admin, optional)* On the Manage page, in **Generate quiz questions** type the topic `phishing emails`, keep **Questions** at 5 and press **Generate**. Wait up to a minute for the questions.

### 10.7 Shutdown checklist (reverse order)

- [ ] **1. Stop the website.** PyCharm: red **Stop** square; terminal: `Ctrl` + `C`; Docker: `docker compose down`.
  *Check-point:* `http://localhost:8000/` no longer opens.
- [ ] **2. Stop the RAG service.** PyCharm: red **Stop** square; terminal: `Ctrl` + `C`. *Check-point:* `http://127.0.0.1:9000/health`
  no longer opens. Documents are kept in `cyberquest-rag/data/chroma/`.
- [ ] **3. Leave the AI model server alone** unless you are its owner (it runs on another machine).
- [ ] **4. Close the terminals.** The `RAG_SERVICE_KEY` you set with `$env:` / `set` is forgotten when the window closes: set it again next time (or store it in the PyCharm run configuration).

### 10.8 Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Knowledge Base says *"The knowledge base service is not running right now. Please try again later."* (HTTP 503) | The RAG service is not running, `RAG_BASE_URL` points to the wrong address or port, the reply took longer than 180 s, or the service answered with something that is not JSON. | Start the RAG service (section 10.3). Open `http://127.0.0.1:9000/health`; it must show `{"ok":true}`. Check `RAG_BASE_URL` in `.env` and **restart the website**. Look in the website window or `logs/cyberquest.log` for `KB service request failed ... (ConnectionError)` (cannot connect) or `(Timeout)`. |
| *"The knowledge base service refused the connection. Ask the Super Admin to check the service key."* | `RAG_SERVICE_KEY` differs between the website's `.env` and the RAG service (or is still `change-me` on one side, or empty on the website). The RAG service answered 401. | Put the **identical** value on both sides. Restart both programs (the website reads `.env` only at start; the RAG service reads its variable at start). |
| RAG window shows `RuntimeError: RAG_SERVICE_KEY is not set` and closes | The variable was not set in that terminal or run configuration. | Set `RAG_SERVICE_KEY` first (section 10.3, "Configure it"), then start again. |
| *"The AI model did not answer. Please try again in a moment."* (the Super Admin sees a technical message such as `Model call failed: ...`) | The AI model server is off or unreachable from your PC, the **API base URL**, **Model ID** or key is wrong, or the model took longer than the **Timeout** setting (default 120 s). | As Super Admin: Manage page → **AI model settings** → fix the values → **Save settings** → **Test connection**. Check network or VPN to `<deepseek-host>:<port>`. Ask the model owner whether the server is running. |
| Answer is *"I couldn't find this in the knowledge base."* | No documents uploaded yet, the question does not match any uploaded text well enough (matches under `RAG_MIN_SCORE`, default 0.2, are dropped), or the document has no readable text. | Check the **Documents** table; upload documents (section 10.6); ask in words used in the documents. |
| Quiz says *"No relevant material in the knowledge base; upload some first"* (404 from the service) | No document matches the topic. | Upload documents, or use a topic that appears in them. |
| Quiz shows *"The model did not return the questions in the expected format..."* and a raw text | The AI did not answer with pure JSON. | Press **Generate** again, or use fewer questions. |
| *"You do not have permission to do this."* (HTTP 403) or the "No access" page on `/kb/manage/` | Your role is not allowed (see the table in section 9.5): guests and students cannot open Manage; teachers cannot delete; only the Super Admin sees AI model settings. The attempt is written to the security log. | Sign in with the right role (section 2 → **Demo logins**). |
| Same 403 message for every action, even for allowed roles | Possibly a CSRF problem because you opened the site on a port or address that is not in `DJANGO_CSRF_TRUSTED_ORIGINS` (not confirmed in the code for every case). | Use `http://localhost:8000` or add your address to `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env` and restart. |
| *"Please sign in again."* / *"Your session has expired. Please sign in again."* (HTTP 401) | Your session ended (sessions last 2 hours). | Sign in again. |
| `/api/kb/...` gives *"We couldn't find that page."* (404) | Wrong address. This project uses `/kb/` and `/kb/api/`, **not** `/api/kb/`. | Use the addresses in section 9.6. |
| Upload error *"Only PDF, TXT and Markdown (.md) files can be uploaded."* | Wrong file type. | Use `.pdf`, `.txt` or `.md`. |
| Upload error *"That file is too large (20 MB maximum)."* (413) | The file is over 20 MB. | Split or shrink the file. |
| Upload error *"No readable text found in the document"* | The PDF is a scan (a picture of text) or empty. | Use a text PDF, a `.txt` or a `.md` file. |
| The first upload or first question is very slow | The search model is downloaded or loaded the first time. | Wait; the next ones are faster. Needs internet on the first run. |
| `Address already in use` / `[WinError 10048]` when starting a part | Another program (or an old copy of the same part) already uses port 9000 or 8000. | Stop the old copy. Find the program: `netstat -ano \| findstr :9000` (the last number is the process id; stop it in Task Manager). Or use another port and update `RAG_BASE_URL` / the CSRF origins (see the "change the port" notes). |
| `'uvicorn' is not recognized...` or `ModuleNotFoundError: No module named 'fastapi'` (or `chromadb`, `pypdf`, `openai`, `sentence_transformers`) | The RAG virtual environment is not activated, or the packages are not installed. | Activate `cyberquest-rag\.venv` (you must see `(.venv)`), then `python -m pip install -r requirements.txt` inside `cyberquest-rag`. |
| `ModuleNotFoundError: No module named 'django'` (or `requests`, `waitress` ...) when starting the website | The project `.venv` is not activated or `requirements` are not installed. | Activate `.venv` in the project root, then `python -m pip install -r requirements-dev.txt`. In PyCharm check the interpreter in **Settings → Project → Python Interpreter**. |
| `ModuleNotFoundError: No module named 'pytest'` when running tests | Test tools are not installed. | `python -m pip install -r requirements-dev.txt`, then `python -m pytest`. |
| Website window shows `no such table` / database errors on first start | Migrations not run. | `python manage.py migrate` then `python manage.py seed_demo`. |
| The RAG service starts but its data seems "gone" | It was started from a different folder, so `RAG_DATA_DIR` (`./data`) pointed to a new empty folder. | Always start it with `cyberquest-rag` as the working directory, or set `RAG_DATA_DIR` to a full path. |
| Knowledge Base works in PyCharm but not in the `run.bat` (Docker) site | Inside Docker `127.0.0.1` is the container, not your PC. | See the Docker note and TODO in section 10.4. |
| `run.bat` says Docker is not installed / not running | Docker Desktop missing or still starting. | Start Docker Desktop and wait until it is ready, or use `run_local.bat`. |
| `Knowledge Base` tab missing | You are not signed in. | Sign in; the tab is shown to every signed-in role. |

When you ask for help, copy the last lines of the RAG window and of the website window (or `logs/cyberquest.log`) and **remove any keys** first.
