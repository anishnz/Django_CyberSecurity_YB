# OOP concepts and design patterns in CyberQuest (Django)

This page shows **where** each concept from the MSE800 course is used, so a marker can open the file and see it.
Paths are relative to the project folder.

## 1. Core OOP concepts

| Concept | Where | What it does |
|---|---|---|
| Classes and objects | `apps/*/models.py`, `apps/*/services.py` | Every table is a model class; every business rule lives in a service class (`PaymentService`, `TicketService`, `BIService` …). |
| Inheritance | `apps/accounts/models.py` `User(AbstractUser)`; `apps/core/exceptions.py` | `User` extends Django's user; 12 error classes extend `CyberQuestError`, so one middleware catches them all. |
| Abstract classes | `Role` (`apps/accounts/roles.py`), `Plan` (`apps/licensing/plans.py`), `QuestionBase` (`apps/learning/questions.py`), `QuizMode` (`apps/quizzes/modes.py`), `Observer` (`apps/notifications/services.py`), `Adapter` / `AIProvider` / `MessageAdapter` (`apps/integrations/adapters.py`) | `ABC` + `@abstractmethod`: the parent says *what* a child must do, each child says *how*. |
| Polymorphism | `user.role_obj.menu()`, `license.plan_obj.is_active(today)`, `adapter.test_connection()`, `ai.generate(prompt)` | The same call works on any role, plan or service – no long `if/elif` chains. |
| Encapsulation | `User._mfa_secret` with `get_mfa_secret()` / `set_mfa_secret()`; `IntegrationSetting._secret` with `get_secret()` / `set_secret()` / `masked` | Secrets are stored encrypted (Fernet) and can only be read through methods; screens only see the masked value. |
| Composition | `QuizService` holds a `LevelProgressionService`; `PaymentService` uses `LicenseService` and `LevelPackService`; `EmailService` uses `IntegrationService` | Big jobs are built from small, testable objects. |
| Value objects / dataclasses | `Quote` (`apps/payments/services.py`), `KeyInfo` (`apps/licensing/keys.py`), `LevelStatus` (`apps/quizzes/progression.py`) | Small immutable or simple data holders with clear names. |
| Properties | `Ticket.is_open`, `Section.is_full`, `MediaFile.visible_to_students`, `AIDraft.teacher_ok` | Rules read like plain attributes. |
| Class and static methods | `SystemSettings.load()`, `FeatureSwitch.is_on()`, `TicketService.handlers_for()` | Helpers that belong to the class, not to one object. |
| Custom exceptions | `apps/core/exceptions.py` | Each error has a friendly message and an HTTP status; users never see a Python traceback. |

## 2. Design patterns

| Pattern | Where | Why |
|---|---|---|
| **Factory** | `QuestionFactory.create()` (`apps/learning/factory.py`), `role_for()` (`apps/accounts/roles.py`), `plan_for()` (`apps/licensing/plans.py`), `IntegrationService.adapter()`, `mode_for()` | One place turns a code (`"single"`, `"teacher"`, `"BASIC"`, `"gmail"`, `"exam"`) into the right object. |
| **Strategy** | `PracticeMode` and `ExamMode` (`apps/quizzes/modes.py`) | Practice and exams pick questions and give feedback differently; the quiz engine does not care which one it has. |
| **Observer** | `NotificationCenter`, `DashboardNotifier`, `LogFileObserver` (`apps/notifications/services.py`) | Services just call `notify("payment_reviewed", …)`; observers decide who gets a dashboard notice or a log line. |
| **Singleton** | `SystemSettings.load()` (`apps/core/models.py`) | There is exactly one row of system settings (pk = 1). |
| **Adapter** | `apps/integrations/adapters.py` | Claude, OpenAI, Gemini, Gmail, Maps, WhatsApp and Viber all look different; each adapter gives the same small interface. The offline helper is a "null object" fallback. |
| **Decorator** | `@role_required`, `@super_admin_required`, `@audit_log`, `@not_read_only` (`apps/accounts/decorators.py`) | Access checks wrap views without changing the view code. |
| **State machine** | `TRANSITIONS` in `apps/helpdesk/services.py`; AI draft status in `apps/ai_assistant/services.py` | Only allowed status moves are possible (for example Open → Waiting is blocked). |
| **Repository / Query objects** | `QuestionQuerySet.approved()`, `.for_practice()` (`apps/learning/models.py`); `visible_to(user)` methods | Database queries are named and reused instead of copied. |
| **Service layer** | every `services.py` | Views stay thin: they read the form, call a service, show the result. |
| **Template (Django templates)** | `templates/base.html` and `partials/` | One layout, reused blocks; the "Explain this page" panel is one partial for every page. |

## 3. Software engineering practices

| Practice | Where |
|---|---|
| Unit and integration tests (pytest-django) | `tests/` – 113 tests, fixed test date, demo data loaded once |
| Static analysis | `.pylintrc` (pylint-django) – 10.00/10 |
| Formatting | `pyproject.toml` (black, 120 characters) |
| Git workflow | `main` ← `develop` ← `feature/<name>-<feature>` branches merged with `--no-ff` |
| Configuration per environment | `cyberquest/settings/base.py`, `dev.py`, `test.py`, `prod.py`, `.env` |
| Containers | `Dockerfile` (non-root user, health check), `docker-compose.yml`, `run.bat` free-port check |
| Logging and monitoring | security log, audit log, email log, `/health/` |
| Security by design | CSP without inline scripts, CSRF, lockout, MFA, encrypted secrets, file-signature upload checks, privacy (first names only in reports) |
| Accessibility | Atkinson Hyperlegible, skip link, alt text, dark mode, larger text |
| Cultural safety | Cultural Guide (Kaiārahi) approval for AI drafts and media with Māori content |
