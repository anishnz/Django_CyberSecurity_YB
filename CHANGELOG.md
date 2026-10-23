# Changelog

All notable changes to CyberQuest (Django). Dates are NZ time.

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
