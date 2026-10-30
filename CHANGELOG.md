# Changelog

All notable changes to CyberQuest (Django). Dates are NZ time.

## [1.1.0] – 2026-10-31 – AI models, WhatsApp test, website pages and fixes

### Added
- Knowledge Base (RAG) by Jihe Qi (pull request #59): Ask page for every role, Manage page for staff (upload
  documents, quiz questions), AI model settings for the Super Admin, and the `cyberquest-rag` FastAPI service.
  Full manual in docs/KNOWLEDGE_BASE.md; product requirements in docs/PRD_CyberQuest.md.
- Knowledge Base review fixes: names and emails removed from questions and quiz topics before the AI; uploads checked
  by content (PDF header, UTF-8 text); 10 questions an hour for guests, 60 for others; Markdown removed from answers.
- run.bat / run.sh start the Knowledge Base as a second Docker container (`rag`); run_local.bat sets it up in its own
  environment and starts it in a small window (optional - CyberQuest runs without it). Random RAG_SERVICE_KEY in .env.
- The RAG service loads the starter knowledge file on its first start; first-start AI model is DeepSeek's public API.
- AI models page (Super Admin): on/off, default model, order, Check and Check all (live-tested with DeepSeek on
  31 Oct 2026). Automatic switch to the next
  model when one fails; default order Gemini → DeepSeek → Claude → OpenAI → Other AI → offline helper.
- DeepSeek and "Other AI" (any OpenAI-compatible service) on the Integrations page.
- WhatsApp test message (Meta `hello_world` template) on the WhatsApp card.
- JSON API v1 for a React front end and an API check page with a Check button per test.
- Team photos, Auckland meetings slider, Our story page, and Business pages (pricing, discount, business case,
  SWOT, proposal, contract sample).

### Fixed
- Docker: added `.dockerignore`. Before, `COPY . .` copied `.env` (secret keys), the local database, uploads and
  logs into the image.
- Jihe Qi's student ID corrected to 271008116 (settings, README, and a data migration for existing databases).
- Error messages in the .bat files showed "[]" instead of "[!]" (delayed expansion removes "!"); now "[ERROR]"/"[NOTE]".
- The RAG service's default AI address pointed to a private developer machine; replaced with DeepSeek's public API.
- Uploaded photos and files showed 404 when DEBUG was off (run.bat / run_local.bat); now served with access rules.
- run_local.bat opened the browser before the server was ready; it now waits for /health/.
- AI connection tests only checked the key; they now ask one tiny question, so they also show when tokens run out.
- Gemini key is sent in a header instead of the URL, so it cannot appear in server logs.
- Colour contrast: comparison table header (Business case) and grey outline buttons now pass WCAG AA.
- AI error messages now include the service's own text; Google's 400 'API key not valid' is shown as a key problem
  (it was shown as 'check the model name'). Test messages no longer repeat the model name.
- AI drafts are asked for plain text, so Markdown stars no longer appear in drafts.

## [1.0.0] – 2026-10-23 – first release

### Sprint 1 – foundation
- Django project with 19 apps, settings for dev / test / prod, `.env` loader, SQLite (PostgreSQL option).
- Docker image (non-root, health check), `docker-compose.yml`, `run.bat` with free-port check, `run_local.bat`, `run.sh`.
- Custom user model with five role classes, login lockout, two-step login (TOTP), Login as, security log, audit log.
- Schools, classes, sections, students, CSV import, system settings with "are you sure?" screen, backups, health check.
- Public website: home with slider, features, levels, pricing, community, about us, contact us, FAQ, privacy.

### Sprint 2 – learning
- Levels, topics and 126 questions imported from the Flask project; question factory with four question types.
- Practice and exam modes (Strategy), scoring, level progression, badges, teacher assignments.
- Licences, Level Packs, product keys, community discount, Observer-based notices.

### Sprint 3 – support, integrations and BI
- Tickets with routing, target times, state machine, attachments and "Report this question".
- Encrypted integrations vault with adapters (Claude, OpenAI, Gemini, Gmail, Google Maps, WhatsApp, Viber), AI test page.
- Email templates, Gmail SMTP, email log, bulk email with unsubscribe, `poll_inbox` auto-reply.
- Business intelligence, school and class reports, CSV / PDF export, Chart.js charts.

### Sprint 4 – payments, certificates and help
- Bank-transfer payments with payslip upload, approval, PDF receipt with GST.
- PDF certificates with QR code, public verify page, section ZIP, share buttons.
- Help centre and "Explain this page", announcements, AI drafts with teacher and Kaiārahi approval.
- Media library with YouTube embeds and cultural check, Google Maps, forgot password by email / WhatsApp / Viber.
- Dark mode and larger text.

### Sprint 5 – quality and release
- Pylint 10.00/10 (`.pylintrc`), black formatting, docstrings, 113 tests, 79% coverage.
- Evidence screenshots per student, full README, `docs/CONCEPTS.md`, this changelog.
- Release ZIP with `run.bat`.
