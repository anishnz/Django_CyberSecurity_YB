# Product Requirements Document (PRD) – CyberQuest

**Learn. Play. Decide. Stay Cyber Safe.**

|                   |                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| Product           | CyberQuest – a cyber-safety learning platform for New Zealand schools                          |
| Document          | Product Requirements Document, baseline for development                                        |
| Version           | 1.0                                                                                            |
| Status            | Approved for development                                                                       |
| Project code      | ``                                                                                              |
| Simulated company | Mount Everest Digital Limited                                                                  |
| Course            | MSE800 Professional Software Engineering – Assessment 2, Yoobee College of Creative Innovation |
| Prepared by       | Jihe Qi with the project team (see the team table in `README.md`)                              |
| Related documents | Product backlog (`docs/backlog/CyberQuest_Product_Backlog.csv`)                                |

## Table of contents

1. [Introduction](#1-introduction)
2. [Problem, goals and success measures](#2-problem-goals-and-success-measures)
3. [Users and roles](#3-users-and-roles)
4. [Scope](#4-scope)
5. [Functional requirements](#5-functional-requirements)
6. [Non-functional requirements](#6-non-functional-requirements)
7. [Business rules and system settings](#7-business-rules-and-system-settings)
8. [Technical constraints and architecture](#8-technical-constraints-and-architecture)
9. [Delivery plan](#9-delivery-plan)
10. [Acceptance and traceability](#10-acceptance-and-traceability)
11. [Assumptions, dependencies and risks](#11-assumptions-dependencies-and-risks)
12. [Open questions](#12-open-questions)

---

## 1. Introduction

### 1.1 Purpose

This document states **what** CyberQuest shall do and the rules it shall follow. It is the reference for design,
development, testing and acceptance. It does not describe how the code is written.

### 1.2 Product summary

CyberQuest teaches cyber safety to students in New Zealand schools. Students study short topics, practise with instant
feedback, sit level exams and earn certificates. Teachers assign exams and read class reports. School Admins run classes,
students and the school's licence. The Super Admin runs the whole platform. A shared **Knowledge Base** lets people ask
questions about uploaded course material and get answers with sources.

CyberQuest is a Django web application that is rebuilt from the team's earlier Flask prototype. It shall run offline-friendly
on a school PC or a single server, with one double-click start on Windows.

### 1.3 Audience of this document

Product owner and client, the four developers, the QA lead, the lecturer and markers.

### 1.4 Conventions

- "**Shall**" = mandatory requirement. "**Should**" = important but can be moved. "**May**" = optional.
- Priority uses MoSCoW: **Must**, **Should**, **Could**, **Won't**. The same scale is used in the product backlog.
- Requirement IDs: `FR-nn` functional, `NFR-nn` non-functional, `KB-nn` Knowledge Base. `US..` refers to a user story in
  the product backlog.
- The user interface of CyberQuest shall be in **English** (New Zealand spelling and plain English); selected te reo Māori
  words are used with the Cultural Guide's approval.

---

## 2. Problem, goals and success measures

### 2.1 Problem

- Children are exposed to scams, phishing, cyberbullying and privacy risks, and many schools have no structured,
  age-appropriate way to teach cyber safety.
- Schools with little IT support, poor internet or small budgets (rural schools, kura) need a tool that is easy to start,
  cheap, works with little internet and respects whānau and Māori values.
- Teachers need quick proof of what students know; School Admins need to manage licences and payments without card
  handling; the vendor needs to run many schools safely.

### 2.2 Goals

| # | Goal |
|---|---|
| G1 | Teach cyber safety through **6 levels** that match year groups, with practice, exams, badges and certificates. |
| G2 | Give each school its own safe space (classes, sections, students) with role-based access and protection of student data. |
| G3 | Let schools pay for what they use: plans, Level Packs, product keys and a fair **50 % community discount**, paid by bank transfer. |
| G4 | Give staff tools: assignments, class reports, tickets, emails, announcements, help centre and AI-assisted drafts with human approval. |
| G5 | Respect Te Tiriti and whānau: cultural approval of Māori content, no public shaming (no leaderboard), family consent. |
| G6 | Be easy to run and operate: one-double-click start, health check, backups, audit and security logs, maintenance mode. |
| G7 | Give everyone a **shared Knowledge Base** to ask questions about course material, with sources, using a hosted AI model. |

### 2.3 Success measures

| Measure | Target |
|---|---|
| A user logs in and lands on the dashboard for their role | 100 % of valid accounts |
| Level exam structure | 4 categories × 5 questions × 5 marks = 100 marks; pass mark 70 % (changeable by the Super Admin) |
| Automated tests | All pass; Pylint score 10/10 on the release |
| Start-up on Windows | One double-click (`run.bat`), free port chosen from 8000 to 8020 |
| No raw Python error is ever shown to a user | 0 tracebacks in the user interface |
| Knowledge Base question without the RAG service running | User sees a friendly English message; the rest of CyberQuest keeps working |

---

## 3. Users and roles

CyberQuest has **five roles**. Every page and action is protected by role; a refused attempt shall show an
"access denied" page and be written to the security log.

| Role | Who | Main needs |
|---|---|---|
| **Super Admin** | Vendor staff | Run the whole platform: schools, licences, payments approval, system settings, integrations, audit and security logs, backups, BI dashboard, "Login as". |
| **School Admin** | Principal / school IT | Classes, sections, teachers and students, family consent, licence, payments, school tickets and announcements. |
| **Teacher** | Classroom teacher | Assign exams, write practice questions, read class reports, approve AI drafts, handle student tickets. |
| **Student** | Child in a consented class | Learn topics, practise, sit exams, earn badges and certificates, raise tickets. |
| **Demo Guest** | Visitor trying the product | Read-only look around; may use the Knowledge Base question box. |

Additional capability: a user flagged as **Cultural Guide (Kaiārahi)** can give the cultural approval for AI drafts and
media with Māori content.

---

## 4. Scope

### 4.1 In scope

Access and accounts · schools and classes · learning content · practice and exams · progression, badges and certificates ·
licensing · bank-transfer payments and receipts · help desk · emails, notices and announcements · reports and business
intelligence · help centre · AI drafts and cultural approval · integrations vault · media library · public website ·
administration and operations · accessibility · **Knowledge Base (RAG question answering)**.

### 4.2 Out of scope (Won't)

| Item | Reason |
|---|---|
| Class leaderboard (US41) | Kaiārahi advice: avoid shaming children. Kept only as a switched-off feature switch. |
| Hands-on hacking labs (US42) | Unsafe and illegal for school students. |
| Card payments | No card details are ever collected; payment is by bank transfer with payslip upload. |
| Per-school Knowledge Bases | The Knowledge Base is **one shared** base for all schools. |
| Saving AI-generated Knowledge Base quiz questions into the question bank | Generated questions are shown on screen for the teacher to read and reuse by hand. |
| Mobile apps | Web only (responsive pages). |

### 4.3 Release phases

| Phase | Content |
|---|---|
| Phase 1 – core platform | Everything in section 5.1 to 5.16 (sprints 1 to 5, see section 9). |
| Phase 2 – Knowledge Base | Section 5.17 and its extra service. The core platform shall work fully without it. |

---

## 5. Functional requirements

### 5.1 Access and accounts (Epic: Access)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-01 | A user shall log in with username and password and land on the dashboard for their role. | Must | US01 |
| FR-02 | After 5 wrong passwords the account shall be locked for 15 minutes; a correct login resets the counter; the event is written to the security log. The limit and time are system settings. | Must | US01 |
| FR-03 | The system shall have five roles (Super Admin, School Admin, Teacher, Student, Demo Guest) with their own permissions. A student opening an admin page shall get "access denied" and the attempt shall be logged. | Must | US02 |
| FR-04 | The system shall refuse login with a friendly reason when: the account is switched off, a temporary account has expired, a student has no recorded family (whānau) consent, the school is switched off, or the school's licence has ended (after any grace days). | Must | US01, US09 |
| FR-05 | Passwords shall contain at least one letter and one number (plus the standard Django checks). Person names shall allow letters (including macrons), spaces, hyphens and apostrophes only. | Must | US01 |
| FR-06 | Admins shall be able to use two-step login (TOTP authenticator app, 6-digit code, one-time backup codes). The Super Admin can switch MFA on or off for any user and can force MFA for admins. | Must | US03 |
| FR-07 | The Super Admin shall be able to "Login as" another user after giving a reason. A red bar shall show who is being viewed, and start and stop shall be in the security log. | Should | US04 |
| FR-08 | Teachers and admins shall reset a forgotten password by email, WhatsApp or Viber. The page shall show the same message for any username, the link shall work once for 1 hour, and requests are limited to 3 per hour. Students are reset by their teacher. | Should | US05 |
| FR-09 | Temporary accounts shall stop working after a set time (15 minutes by default, 5 to 240 minutes, changeable by the Super Admin). | Should | – |

### 5.2 Schools, classes and people (Epic: Schools)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-10 | The Super Admin shall add schools; a new school shall get a clean code and a free 30-day trial licence. | Must | US06 |
| FR-11 | A School Admin shall manage classes and sections. A section holds **35 students by default**; adding one more shall show "section is full". Only the Super Admin can change the capacity (1 to 60). | Must | US07 |
| FR-12 | A School Admin shall import students from a CSV file; a preview with errors shall be shown before anything is saved. | Should | US08 |
| FR-13 | A School Admin shall record family consent. Students without consent shall be listed on the School Admin dashboard and shall not be able to log in. | Must | US09 |
| FR-14 | A school's plan shall limit how many sections it can add; exceeding it shall show a clear message about upgrading. | Must | US16 |

### 5.3 Learning content (Epic: Learning)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-15 | The product shall offer **6 levels** matching year groups; Level 1 (Year 7) is free. | Must | US10 |
| FR-16 | Content shall be organised into topics (24 at release) and questions (126 at release) in 15 categories. Each level uses a defined set of categories. | Must | US10 |
| FR-17 | A topic page shall show the text, good habits, a Kiwi example and any approved media; te reo Māori labels shall be used where approved. | Must | US11 |
| FR-18 | Question types shall be single answer, multi-select, true/false and scenario. | Must | US12 |
| FR-19 | Learning content shall be loadable from JSON files (content import) and demo data shall be loadable with `seed_demo`. | Should | – |
| FR-20 | A teacher shall write extra practice questions for their own school (2 to 4 answers and feedback). These are used only in that school's practice. | Should | US15 |
| FR-21 | A student shall be able to report a question that looks wrong; the teacher receives a content ticket linked to the question. | Should | US21 |

### 5.4 Practice, exams and progression

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-22 | **Practice**: after each answer the student shall see right or wrong, the reason and a safety tip. Practice never counts against the student. | Must | US12 |
| FR-23 | **Level exam**: 4 categories × 5 questions × 5 marks = 100 marks. 70 % or more passes. | Must | US13 |
| FR-24 | A teacher shall assign a level exam to a section with a due date. Students of that section see the exam button and get a notice. | Must | US14 |
| FR-25 | The result shall show a percentage and an awareness level: Excellent (90 or more), Good (75 or more), Developing (50 or more), Needs more practice (below 50). The word "Fail" shall never be shown. | Must | US13 |
| FR-26 | A student moves up when the best exam at the current level reaches the pass mark **and** the school owns the next Level Pack. A level trail shall show each level as Passed, Open, Locked (pass the level before) or "Ask your teacher about this level". | Must | US10 |
| FR-27 | Badges shall be awarded: Cyber Starter (L1), Cyber Explorer (L2), Cyber Defender (L3), Cyber Guardian (L4), Cyber Senior (L5), Cyber Pro (L6) and Perfect Score. | Should | US10 |
| FR-28 | A PDF **certificate** with a QR code shall be created for each passed level. A public verify page shall show the student's **first name only**. Teachers can download certificates as a ZIP. | Must | US30 |

### 5.5 Licensing and Level Packs (Epic: Licences)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-29 | Plans shall follow the table in section 7.2 (Trial, Basic, Standard, Unlimited): section limit, monthly price and grace days. Level Packs for Levels 2 to 6 are bought separately at the prices in section 7.2. | Must | US16 |
| FR-30 | The Super Admin shall be able to switch a **50 % community discount** on or off for a school (plan prices only). | Must | US17 |
| FR-31 | A school shall be able to activate or change its plan with a **product key** that works without internet; a key with a wrong check code is rejected and logged. | Should | US18 |
| FR-32 | The system shall send a "licence expiring" notice at most once a day per school during the warning period (14 days by default, 1 to 60, set by the Super Admin). Unlimited plans are never warned. | Should | – |

### 5.6 Payments (Epic: Payments)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-33 | A School Admin shall get a quote for a plan (1, 3, 6 or 12 months) or a Level Pack with **15 % GST** added, pay by bank transfer and upload a payslip (PDF, JPG or PNG; type checked by file signature). | Must | US28 |
| FR-34 | The Super Admin shall approve or reject payslips. Approval starts the plan or pack at once and makes a PDF tax receipt; rejection needs a reason. | Must | US29 |
| FR-35 | No card details shall ever be collected or stored. | Must | US28 |

### 5.7 Help desk (Epic: Communication)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-36 | Every role shall be able to raise a ticket. A ticket gets a number (CQ-0001 format). | Must | US20 |
| FR-37 | Routing: Student → their teachers; Teacher → School Admin; School Admin, website and email → Super Admin. The Super Admin sees all tickets. | Must | US20 |
| FR-38 | Target times (SLA): Urgent 4 hours, High 1 day, Normal 3 days, Low 5 days. | Must | US20 |
| FR-39 | Status moves shall follow an allowed set only (Open, Assigned, In progress, Waiting, Resolved, Closed). A closed ticket can be reopened within 7 days; after that a new ticket shall be opened. | Must | US20 |
| FR-40 | Tickets shall support comments, internal notes (staff only), attachments (PDF, JPG, PNG; up to 3 files per comment) and a history. | Must | US20 |
| FR-41 | A visitor without an account shall be able to raise a ticket from the website; support emails shall become tickets with an automatic reply (`poll_inbox` command). | Should | US22 |

### 5.8 Notices, email and announcements

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-42 | Events (exam assigned, level unlocked, payment reviewed, ticket events, licence updated) shall create dashboard notices for the right people; a bell shows the unread number. A failing notice channel shall never stop the others. | Must | US19 |
| FR-43 | The Super Admin shall edit email templates. Emails shall go through Gmail SMTP when set up; otherwise they go to the console and the email log and nothing breaks. | Should | US22 |
| FR-44 | A School Admin shall send bulk email to opted-in parents with a recipient count preview and an unsubscribe link. | Should | US23 |
| FR-45 | Admins shall post announcements (Pānui) for one school or everyone, shown only to the chosen audience and only between the chosen dates. | Should | US32 |

### 5.9 Reports and business intelligence (Epic: Reports)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-46 | A teacher shall see class reports with the weakest topics first, one row per student with **first names only**, and download them as CSV and PDF. | Must | US27 |
| FR-47 | The Super Admin shall see a business intelligence dashboard: schools, students, exams, pass rate, income per month, plan mix, weakest categories, tickets and payments to review. | Should | US26 |

### 5.10 Help centre

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-48 | Every page shall have an **"Explain this page"** button showing the guide for the user's role, with a question box for the helper. A help centre with articles and a first-login tour shall be provided, in plain English. | Should | US31 |

### 5.11 AI drafts and cultural approval (Epic: AI)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-49 | A teacher shall be able to ask for AI drafts (question, tip, parent message, explanation). Names and email addresses shall be removed before anything is sent to an AI service. | Could | US33 |
| FR-50 | A draft shall not be published without **teacher approval**. Where Māori content is found, it also needs the **Cultural Guide (Kaiārahi)** approval and stays hidden until then. | Must | US33, US34 |
| FR-51 | Without an AI key the system shall still work using an offline helper that makes simple drafts. | Should | US25 |

### 5.12 Integrations (Epic: Integrations)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-52 | The Super Admin shall have one page to add keys for Claude, OpenAI, Gemini, Gmail, Google Maps, WhatsApp and Viber. Keys are stored encrypted, shown masked, tested with a button, and every change is logged. | Should | US24 |
| FR-53 | The Super Admin shall have an AI test page to check that an AI key works. | Could | US25 |

### 5.13 Media library (Epic: Media)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-54 | Teachers shall upload images (JPG, PNG, WebP, GIF), audio (MP3, OGG, WAV, M4A), video (MP4, WebM, QuickTime) and PDF, and add YouTube videos that play in privacy mode (youtube-nocookie.com). | Should | US35 |
| FR-55 | Uploads shall be checked by **file signature**, not by file name, and against a size limit set by the Super Admin. A rejected upload shall be written to the security log. | Must | US35 |
| FR-56 | Media with Māori content shall need Cultural Guide approval before students see it. | Must | US34 |

### 5.14 Public website (Epic: Website)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-57 | A public website shall explain the problem, real NZ facts and law, the solution, features, pricing and architecture, and offer an about and contact page. | Should | US39 |
| FR-58 | The school page shall offer free share buttons (WhatsApp, Viber, Facebook) and a Google Map. | Could | – |

### 5.15 Administration and operations (Epic: Operations)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-59 | The system shall have a **health check** at `/health/` that checks database, free disk space (more than 0.5 GB) and a writable media folder (HTTP 200 when healthy, 503 otherwise) and lists optional integrations without failing. | Must | US37 |
| FR-60 | The Super Admin shall make database backups and restore them with a typed confirmation word. | Must | US37 |
| FR-61 | The Super Admin shall use **feature switches** to turn features on or off, and **maintenance mode** with a message (the Super Admin can still sign in). | Must | US37 |
| FR-62 | System settings shall be held in one settings record. Overwriting settings shall show an "are you sure?" screen first. | Must | US37 |
| FR-63 | An **audit log** (who changed what, old and new value) and a **security log** (logins, lockouts, access denied, rejected uploads, MFA changes, Login as) shall be kept and viewable by the Super Admin. | Must | US37 |
| FR-64 | **One double-click start**: `run.bat` (Docker) picks a free port from 8000 to 8020, creates `.env` with random secrets, waits for `/health/` and opens the browser; `run_local.bat` does the same without Docker; `run.sh` for macOS and Linux. | Must | US38 |
| FR-65 | Demo data shall be loadable (four sample schools, users of every role, results) and resettable by the Super Admin with a typed confirmation word. A demo accounts page shall be shown only while demo mode is on. | Should | US38 |

### 5.16 Accessibility and quality (Epic: Quality)

| ID | Requirement | Priority | Story |
|---|---|---|---|
| FR-66 | The user interface shall offer **dark mode** and **larger text** buttons and remember the choice. | Could | US36 |
| FR-67 | The interface shall use the Atkinson Hyperlegible font, visible keyboard focus, a skip link and alt text for images. | Should | US36 |
| FR-68 | The release shall come with automated tests, a Pylint score of 10/10 and evidence screenshots per student. | Must | US40 |

### 5.17 Knowledge Base (RAG question answering)

The **Knowledge Base (KB)** is one shared library of course documents. People ask a question in plain English; the system
finds the most relevant parts of the documents and a hosted AI model writes a short answer with the sources used.

| ID | Requirement | Priority |
|---|---|---|
| KB-01 | The top navigation shall show a **Knowledge Base** tab for every logged-in role, including the Demo Guest. | Must |
| KB-02 | There shall be an **Ask page** (`/kb/`) where the user types a question (up to 1000 characters) and sees an **answer** and the **sources** (document title and a short passage) that the answer used. | Must |
| KB-03 | If the documents do not contain the answer, the system shall say so instead of inventing one. For a student the answer shall be clear, short and age-appropriate. The Ask page shall warn that AI answers can contain mistakes. | Must |
| KB-04 | There shall be a **Manage page** (`/kb/manage/`) for Teacher, School Admin and Super Admin. | Must |
| KB-05 | **Upload documents** (Teacher, School Admin, Super Admin): the supported file types are `.txt`, `.md` and `.pdf`, up to 20 MB each, with a title and optional tags. The system shall split the text into chunks, store them for search, and report how many chunks were made. | Must |
| KB-06 | **List documents**: the Manage page shall list all documents (title, tags, number of chunks). | Must |
| KB-07 | **Delete a document** shall be allowed only for **School Admin and Super Admin**. A Teacher shall not see or use the delete button. | Must |
| KB-08 | **Generate quiz questions** (Teacher, School Admin, Super Admin): the user gives a topic (up to 300 characters), a number of questions (1 to 20) and a difficulty (Easy, Medium or Hard); the system returns multiple-choice questions with the correct answer and an explanation, based on the documents, shown on screen for the teacher to read before using in class. They are not saved into the question bank. | Should |
| KB-09 | **Model settings** (Super Admin only): display name, API base URL, model ID, API key, temperature, maximum answer length (max tokens) and timeout; plus a **Test connection** button. The API key shall be shown only in masked form after saving; leaving the key field empty keeps the current key. | Must |
| KB-10 | There shall be **one Knowledge Base for all schools**. No question or document is tied to a single school. | Must |
| KB-11 | The role shall be decided by CyberQuest (never by the browser) and shall be checked **again** by the Knowledge Base service. A refused action shall show a friendly message and be written to the security log. | Must |
| KB-12 | The browser shall talk only to CyberQuest. The service secret shall never be sent to the browser. | Must |
| KB-13 | When the Knowledge Base service or the AI model cannot be reached, or takes too long, the user shall see a friendly English message and the rest of CyberQuest shall keep working. | Must |
| KB-14 | Text that comes from the service or the AI shall be shown as plain text, never as HTML. | Must |
| KB-15 | Uploading and deleting documents and changing model settings shall be written to the audit log. | Should |
| KB-16 | The Demo Guest is otherwise read-only, but shall still be able to ask questions (asking changes no data). | Should |

Permission matrix for the Knowledge Base:

| Action | Guest | Student | Teacher | School Admin | Super Admin |
|---|---|---|---|---|---|
| See the Knowledge Base tab and Ask page | Yes | Yes | Yes | Yes | Yes |
| Ask a question | Yes | Yes | Yes | Yes | Yes |
| Open the Manage page | No | No | Yes | Yes | Yes |
| Upload a document | No | No | Yes | Yes | Yes |
| List documents | No | No | Yes | Yes | Yes |
| Generate quiz questions | No | No | Yes | Yes | Yes |
| Delete a document | No | No | No | Yes | Yes |
| Change model settings / test connection | No | No | No | No | Yes |

Technical rules for the Knowledge Base:

- Django proxies every call under `/kb/api/` to the Knowledge Base service. The service address and shared key come from
  the settings `RAG_BASE_URL` (default `http://127.0.0.1:9000`) and `RAG_SERVICE_KEY`.
- Django waits 5 seconds to connect and up to 180 seconds for an answer.
- Uploaded text is split into chunks of about 800 characters (120 overlap), stored in a local vector database, and the
  best matching chunks (default 5) are sent to the AI model as the only context.
- The AI model is reached through an OpenAI-compatible Chat Completions API (first-start default since 1.1.0: DeepSeek's
  public API, model `deepseek-chat`). Its address is a model setting that the Super Admin can change.
- The Knowledge Base service runs on port 9000 (run_local.bat: first free port from 9000 to 9020; Docker: the `rag`
  container) and is not part of the Django site; the rest of CyberQuest works without it.

---

## 6. Non-functional requirements

| ID | Requirement | Priority |
|---|---|---|
| NFR-01 | **Security of sign-in.** Passwords shall have at least one letter and one number (plus Django's standard checks). After 5 wrong passwords an account shall be locked for 15 minutes. Sessions shall end after 2 hours. | Must |
| NFR-02 | **Friendly errors.** Users shall never see a Python error page; errors shall show a clear English message (403, 404, 500 and licence/lock/read-only pages). | Must |
| NFR-03 | **Browser protection.** Every page shall send a Content Security Policy (scripts only from the site itself), a Permissions-Policy, no framing (`X-Frame-Options: DENY`) and no content-type sniffing. | Must |
| NFR-04 | **Safe uploads.** An upload shall be accepted only when its real file type (checked from the file's first bytes) is allowed and its size is under the limit. Default limits: image 5 MB, audio 20 MB, video 100 MB, document 10 MB, payslip 5 MB, CSV 2 MB. Rejected uploads shall be written to the security log. | Must |
| NFR-05 | **Secrets.** Secrets and API keys shall not be stored in the code. Integration keys shall be stored encrypted; `.env` shall never be committed. | Must |
| NFR-06 | **Language and time.** The interface shall be in English (New Zealand) and use the Pacific/Auckland time zone. Māori words (for example Pānui, Tautoko) shall be used with their English meaning nearby. | Must |
| NFR-07 | **Logging.** Events shall be written to a rotating log file (1 MB per file, 3 old files kept) and security events to the security log table. | Should |
| NFR-08 | **Easy start for schools.** A school with little IT support shall be able to start the site with one double-click (Docker) or without Docker with a second script. | Must |
| NFR-09 | **Quality.** The code shall follow the team style (Black, line length 120) and Pylint, and shall be covered by automated tests. | Must |
| NFR-10 | **Isolation of optional services.** If the Knowledge Base service or the AI model is down, only the Knowledge Base shall be affected. | Must |

---

## 7. Business rules and system settings

### 7.1 System settings (Super Admin can change; default and allowed range)

| Setting | Default | Range |
|---|---|---|
| Default students per section | 35 | 1 to 60 |
| Exam pass mark (%) | 70 | 50 to 100 |
| Questions in a practice quiz | 10 | 5 to 20 |
| Temporary account time (minutes) | 15 | 5 to 240 |
| Licence warning (days before the end) | 14 | 1 to 60 |
| Upload limits (MB): image / audio / video / document | 5 / 20 / 100 / 10 | 1 to 20 / 1 to 50 / 5 to 500 / 1 to 25 |
| Force two-step login for admins | Off | On or Off |
| Maintenance mode and message | Off | On or Off, message up to 200 characters |

The Super Admin shall also be able to change the contact email and phone, the welcome video link and the bank account name, number and GST number shown on the payment page and receipts.

### 7.2 Plans, prices and Level Packs (NZD, before GST)

| Plan | Sections | Price per month | Grace days |
|---|---|---|---|
| Free Trial | 1 (30 days) | 0 | 0 |
| Basic | 5 | 100 | 7 |
| Standard | 15 | 250 | 7 |
| Unlimited | No limit (never expires) | 500 | – |

| Level Pack | Price |
|---|---|
| Level 2, 3, 4 | 150 each |
| Level 5 | 250 |
| Level 6 | 400 |

- Level 1 is free for every school.
- GST of 15% shall be added to every quote and receipt. A 50% community discount shall apply to plan prices only (not to Level Packs).
- A plan payment shall be for 1, 3, 6 or 12 months. The payment date shall be within the last 60 days.
- A school shall not have two payments of the same kind waiting for review at the same time.

### 7.3 Learning and exams

- Content: 6 levels, 24 topics, 126 questions in 15 categories. Question types: single answer, multi-select, true/false and scenario.
- A level exam has 20 questions (5 from each of 4 categories), 5 marks each, 100 marks in total. Questions are chosen at random from approved questions.
- A student moves up when the best exam at the current level reaches the pass mark **and** the school owns the next Level Pack.
- Results use awareness levels: Excellent (90 or more), Good (75 or more), Developing (50 or more), Needs more practice (below 50). The word "Fail" shall never be shown.
- Badges: one per level (Cyber Starter, Cyber Explorer, Cyber Defender, Cyber Guardian, Cyber Senior, Cyber Pro) and a Perfect Score badge.

### 7.4 Roles

| Role | Short description |
|---|---|
| Super Admin | Runs the whole platform: schools, licences, payments, settings, integrations, audit and security logs, backups. |
| School Admin | Runs one school: classes, sections, people, licence and payments, reports, announcements. |
| Teacher | Teaches sections: assigns exams, writes school questions, sees class reports, answers student help requests. |
| Student | Learns: topics, practice, exams, badges, certificates, help requests. |
| Guest | Read-only demo visitor; cannot change data. |

---

## 8. Technical constraints and architecture

| Topic | Requirement |
|---|---|
| Framework | Django 5.2 (Python 3.10 or newer); the Docker image uses Python 3.12. |
| Database | SQLite by default; PostgreSQL as an option (`DATABASE_ENGINE`). |
| Web server | `waitress` in Docker and in the no-Docker script; Django's development server for developers. |
| Static files | Served by WhiteNoise. |
| Code structure | One Django app per area under `apps/`, with business rules in service classes rather than in views. |
| Runtime packages | As listed in `requirements.txt`; developer tools in `requirements-dev.txt`. |
| Configuration | A `.env` file read by the settings; secrets are never committed. |
| Time zone and language | `Pacific/Auckland`, `en-nz`. |
| Start-up | `run.bat` (Docker), `run_local.bat` (no Docker), `run.sh` (macOS / Linux). |

### 8.1 Knowledge Base architecture

```
 Browser  --->  CyberQuest Django site (port 8000, apps/kb proxy at /kb/)
                     --->  RAG service (FastAPI, port 9000)
                                 --->  AI model server (DeepSeek, OpenAI-compatible API)
```

- The browser shall talk only to the Django site. Django is the only caller of the RAG service.
- Django shall send a shared secret and the user's role to the RAG service; the RAG service shall check both again.
- There is **one** shared knowledge base for all schools.

---

## 9. Delivery plan

The work shall be delivered in five sprints; the Knowledge Base follows as a separate phase (section 4.3).

| Sprint | Theme | Content |
|---|---|---|
| 1 | Foundation | Project set-up, Docker and start-up scripts, accounts and roles, login security, schools, classes and sections, settings, backups, health check, public website. |
| 2 | Learning | Levels, topics and questions, practice and exam modes, scoring, progression, badges, assignments, licences and Level Packs. |
| 3 | Support, integrations and BI | Tickets, integrations vault, email, reports and charts. |
| 4 | Payments, certificates and help | Bank-transfer payments and receipts, certificates, help centre, announcements, AI drafts, media library, forgot password, dark mode and larger text. |
| 5 | Quality and release | Tests, code-quality checks, evidence, documentation, release package. |
| Phase 2 | Knowledge Base | Section 5.17 and the separate RAG service. |

---

## 10. Acceptance and traceability

Each requirement is accepted when its acceptance criteria in `docs/backlog/CyberQuest_Product_Backlog.csv` (user stories US01 to US42) are met and the automated tests pass.

| Area | Requirements | Stories |
|---|---|---|
| Access and accounts | FR-01 to FR-09 | US01 to US05, US09 |
| Schools, classes and people | FR-10 to FR-14 | US06 to US09, US16 |
| Learning content | FR-15 to FR-21 | US10 to US12, US15, US21 |
| Practice, exams and progression | FR-22 to FR-28 | US10, US12, US13, US14, US30 |
| Licensing and Level Packs | FR-29 to FR-32 | US16 to US18 |
| Payments | FR-33 to FR-35 | US28, US29 |
| Help desk | FR-36 to FR-41 | US20, US22 |
| Notices, email and announcements | FR-42 to FR-45 | US19, US22, US23, US32 |
| Reports and business intelligence | FR-46 to FR-47 | US26, US27 |
| Help centre | FR-48 | US31 |
| AI drafts and cultural approval | FR-49 to FR-51 | US25, US33, US34 |
| Integrations | FR-52 to FR-53 | US24, US25 |
| Media library | FR-54 to FR-56 | US34, US35 |
| Public website | FR-57 to FR-58 | US39 |
| Administration and operations | FR-59 to FR-65 | US37, US38 |
| Accessibility and quality | FR-66 to FR-68 | US36, US40 |
| Knowledge Base | KB-01 to KB-16 | Accepted by the criteria below |

Knowledge Base acceptance criteria:

1. Given any signed-in user, when they ask a question the documents can answer, then they see an answer and at least one source.
2. Given a question the documents cannot answer, then the answer says so and no source is shown.
3. Given a Teacher, when they upload a PDF, TXT or Markdown file up to 20 MB, then it appears in the document list; any other type or a larger file is refused.
4. Given a Teacher, then there is no Delete button; given a School Admin or Super Admin, then Delete works after confirmation.
5. Given a non-Super Admin, then the model settings are not shown and the endpoints answer 403.
6. Given the RAG service or the AI model is switched off, then the user sees a friendly message and the rest of CyberQuest keeps working.

---

## 11. Assumptions, dependencies and risks

### 11.1 Assumptions and dependencies

- Schools have a modern browser; the School IT person may have little IT support, so start-up shall need one double-click.
- Docker Desktop (or Python 3.10 or newer for the no-Docker start) is available on the machine that runs the site.
- Payment is by bank transfer and checked by hand; no card payment service is used.
- Gmail, WhatsApp, Viber, Google Maps and AI keys are optional; every feature that needs one shall have a fallback.
- The Knowledge Base needs a separate RAG service and an AI model server that the owner keeps running; the AI model is reached over a private network.

### 11.2 Risks

| Risk | Effect | Mitigation |
|---|---|---|
| The AI model gives a wrong or unsuitable answer | Misleading advice for students | Answers use only the uploaded documents; "not in the documents" is allowed; the Ask page warns that answers can be wrong; staff choose the documents. |
| The RAG service or the AI model is switched off | Knowledge Base unavailable | Friendly message; the rest of CyberQuest is not affected (NFR-10). |
| A secret leaks (service key, API keys) | Misuse of the service | Keys in `.env` or the encrypted vault, never in the browser, never committed. |
| A harmful file is uploaded | Security risk | File type checked by signature or extension and size limit; rejected uploads logged. |
| Children's data | Privacy harm | First names only in reports and certificate checks; family consent before a student can log in; no card data. |
| Māori content used wrongly | Cultural harm | Cultural Guide approval before such content is shown. |

---

## 12. Open questions

| # | Question | Owner |
|---|---|---|
| 1 | Should quiz questions generated by the Knowledge Base be saved into the question bank after teacher approval? | Product owner |
| 2 | Should the Knowledge Base later use per-school documents? (Release 1 uses one shared knowledge base.) | Product owner |
| 3 | Which additional file types (for example Word) are needed? | Teachers |
