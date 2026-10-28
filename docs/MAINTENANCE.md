# CyberQuest – Maintenance Document

Version 1.0.0 · Mount Everest Digital Solution Ltd. · Owner: Anish Shrestha (Team Lead)

This document says **how CyberQuest is kept running, safe and up to date after release**. Setup and features are in
`README.md`; packages are in `docs/REQUIREMENTS_EXPLAINED.txt`. They are not repeated here.

## 1. Maintenance types

| Type | Meaning | CyberQuest example | Owner |
|---|---|---|---|
| Corrective | Fix a bug | A ticket says a question has the wrong answer → fix in `data/`, run `import_content` | Jihe (QA) + content owner |
| Adaptive | Change for a new environment | New Django or Python version; move from SQLite to PostgreSQL (`DATABASE_ENGINE=postgres`) | Rajneesh |
| Perfective | Improve or add features | New Level Pack, new report chart, full te reo Māori version | Dinesh / Anish |
| Preventive | Stop future problems | Update packages, rotate keys, test a backup restore, keep Pylint 10/10 | Anish |

## 2. Routine checklist

| When | Task | How |
|---|---|---|
| Daily (school day) | Check the app is up | Open `/health/` → `{"status": "ok"}` |
| Daily | Answer new tickets | Super Admin → Tickets; keep target times |
| Weekly | Make a backup | Super Admin → System → Backups → **Make backup** (keeps the last 10) |
| Weekly | Read the security log | Look for many failed logins, Login as, key changes |
| Monthly | Copy one backup off the computer | Copy `backups/` (or the Docker volume `cyberquest_backups`) to a USB drive or school drive |
| Monthly | Approve payslips and check licences | Payments → waiting; Licences → expiring soon |
| Every 3 months | Update packages | Follow section 3 of `docs/REQUIREMENTS_EXPLAINED.txt` |
| Every 3 months | Test a restore | Restore a backup on a test copy (type **RESTORE**) and log in |
| Every 6 months | Rotate secrets | New `DJANGO_SECRET_KEY`; re-enter API keys on the Integrations page |
| Each school year | Content review | Update questions and NZ law facts; Kaiārahi (Cultural Guide) checks Māori content |

## 3. Change process (every fix or feature)

```
Ticket or GitHub issue → feature branch → code + tests → pytest + Pylint → pull request
→ review by another member → merge into develop → merge into main → tag release → update CHANGELOG.md
```

- Branch name: `feature/<name>-<feature>` or `fix/<name>-<bug>`.
- Commit message: `type(scope): short text [Role – Name]`, for example `fix(help): pass mark is 70% [QA – Jihe]`.
- Version numbers: `MAJOR.MINOR.PATCH` (1.0.1 = bug fix, 1.1.0 = new feature, 2.0.0 = breaking change).

## 4. Common jobs

| Job | Command or screen |
|---|---|
| Start / stop (Docker) | `run.bat` / `docker compose down` |
| Start without Docker | `run_local.bat` |
| Apply database changes after an update | `python manage.py migrate` (Docker does this on start) |
| Load or update learning content | `python manage.py import_content` |
| Reset demo data | Super Admin → System → **RESET DEMO** (typed confirmation) or `python manage.py seed_demo` |
| Turn support emails into tickets | `python manage.py poll_inbox` (schedule with Windows Task Scheduler) |
| Maintenance mode | Super Admin → Settings → `maintenance_mode` on (users see a friendly page) |
| Switch a feature off | Super Admin → System → Feature switches |
| Read the app log | `logs/cyberquest.log` (3 rotating files of 1 MB each) |

## 5. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| "Ports 8000–8020 are all busy" | Other programs use the ports | Close them, or set `HOST_PORT` in `.env` |
| Browser does not open | `/health/` did not answer in time | Wait, then open the address shown in the black window |
| "Docker is not running" | Docker Desktop is closed | Start Docker Desktop, run `run.bat` again |
| Locked out after 5 wrong passwords | Lockout rule (15 minutes) | Wait 15 minutes, or use Forgot password (a password reset also clears the lock) |
| Lost MFA phone | No codes | Use a backup code, or Super Admin switches MFA off for that user |
| AI draft is very simple | No AI key, offline helper is used | Add a key on the Integrations page (optional) |
| Upload rejected | Real file type does not match, or file too big | Use a real JPG/PNG/PDF within the size limit |

## 6. Security maintenance

- Never put API keys in `.env` or Git; only on the Integrations page (encrypted).
- `DEBUG` is off in production (`prod.py`). When hosted with a certificate, set `HTTPS=1` in `.env` to turn on secure cookies, SSL redirect and HSTS.
- Review user accounts each term; deactivate staff who have left.
- If a breach is suspected: maintenance mode on → change secrets → read security and audit logs → restore a clean
  backup if needed → tell the school. Under the Privacy Act 2020, a serious privacy breach must be reported to the
  Privacy Commissioner and the affected people.

## 7. Support levels

| Priority | Example | Target time |
|---|---|---|
| Urgent | Nobody can log in | 4 hours |
| High | Exams cannot be submitted | 1 day |
| Normal | A question looks wrong | 3 days |
| Low | Idea for a new feature | 5 days |

These are the service targets (SLA) set in `apps/helpdesk/services.py`.

## 8. Handover

A new maintainer needs: GitHub access (collaborator), this document, `README.md`, `docs/CONCEPTS.md`, the Super Admin
login, and the backup location. Run `python -m pytest` first: all tests must pass before any change.
