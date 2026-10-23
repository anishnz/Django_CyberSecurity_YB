"""
content.py - Starting help articles and the guided tour for each role
=====================================================================

Owner: Dinesh Upreti with Jihe Qi (checked against the screens in manual testing).
Plain English (NFR-07). Words in te reo Māori were checked by the Cultural Guide
(Kaiārahi) role in the team's simulated review.
"""

STAFF = "super_admin,school_admin,teacher"
ADMINS = "super_admin,school_admin"

# slug: (title, audience, pages, summary, body, order)
ARTICLES = {
    "welcome": (
        "What is CyberQuest?",
        "super_admin,school_admin,teacher,student,guest",
        "website:home,accounts:home",
        "A cyber safety learning game for New Zealand schools: six levels, practice, exams and certificates.",
        "CyberQuest helps ākonga (students) learn to stay safe online through short lessons and quizzes.\n\n"
        "- **Learn** each topic, then **practise** with feedback after every answer.\n"
        "- Sit the **level exam** (20 questions, 100 marks). Pass to unlock the next level and get a certificate.\n"
        "- Teachers assign exams and see class reports. School Admins run classes and the licence.\n\n"
        "Level 1 is free for every school. Levels 2 to 6 come with Level Packs.",
        1,
    ),
    "student-dashboard": (
        "My levels",
        "student",
        "quizzes:student_dashboard,quizzes:level",
        "Your learning trail. Open levels are coloured; locked levels show a padlock.",
        "Start with the first open level. Read each topic, then press **Practise**.\n\n"
        "- Practice never counts against you – try as often as you like.\n"
        "- The **exam** button appears when your teacher assigns the exam.\n"
        "- Pass mark is 60 % (your school can change it). Pass to unlock the next level.",
        10,
    ),
    "practice-and-exams": (
        "Practice and exams",
        "student,teacher",
        "quizzes:question,quizzes:feedback,quizzes:result,quizzes:topic",
        "How questions, feedback and scores work.",
        "In **practice** you see feedback straight after each answer, with a safety tip.\n\n"
        "In an **exam** you see your score at the end. Each exam has 4 categories × 5 questions.\n\n"
        "- If a question looks wrong, use **Report this question** (practice only).\n"
        "- Your awareness level is Excellent (90 %+), Good (75 %+), Developing (50 %+) or Beginning.",
        11,
    ),
    "certificates": (
        "Certificates",
        "student,teacher,school_admin",
        "certificates:my_certificates,quizzes:my_results",
        "Download a PDF certificate for every level you pass.",
        "Each certificate has a QR code and a short code. Anyone can scan it to check it is real – the check page "
        "shows your first name only.\n\nTeachers can download all certificates for a section as one ZIP file "
        "from the class report.",
        12,
    ),
    "teacher-dashboard": (
        "Teacher dashboard",
        "teacher",
        "quizzes:teacher_dashboard",
        "Your sections, recent exam results and notices.",
        "- **Assignments**: choose a section and a level to let students sit the exam. A due date is optional.\n"
        "- **My questions**: write extra practice questions for your school.\n"
        "- **AI drafts**: ask the AI helper for a draft; you and the Cultural Guide approve it first.\n"
        "- **Reports**: class results with CSV and PDF download.",
        20,
    ),
    "assignments": (
        "Assigning level exams",
        "teacher",
        "quizzes:assignment_list",
        "Students can only sit a level exam after you assign it to their section.",
        "Pick the section, the level and (optional) a due date, then press **Assign**. Students get a notice.\n\n"
        "Removing an assignment does not delete results that were already finished.",
        21,
    ),
    "questions": (
        "Writing practice questions",
        "teacher,super_admin",
        "learning:my_questions,learning:question_new,learning:question_edit,learning:level_list",
        "Add your own practice questions with 2–4 answers and feedback.",
        "Every question needs clear feedback that teaches the safe choice. Keep names and places made-up.\n\n"
        "- Single answer, multiple answer and true/false types are supported.\n"
        "- Your questions are used in practice for your school only (not in exams).",
        22,
    ),
    "reports": (
        "Reports and BI",
        STAFF,
        "reports:bi_dashboard,reports:school_bi,reports:class_report_pick,reports:class_report,reports:student_report",
        "Numbers that show how students are doing, and how the business is doing.",
        "- **Class report**: one row per student – level, best score, last exam, family consent.\n"
        "- **Categories to practise** shows the weakest topics first, so you know what to teach next.\n"
        "- **Business intelligence** (Super Admin): schools, income, plans, tickets and payments.\n\n"
        "Reports show first names and usernames only. Parent details never appear.",
        23,
    ),
    "school-admin": (
        "Running your school",
        "school_admin",
        "schools:admin_dashboard,schools:class_list,schools:student_list,schools:teacher_list,schools:student_import",
        "Classes, sections, students, teachers and family consent.",
        "- Make **classes** (for example Year 7) and **sections** (7A, 7B). A section holds up to 35 students.\n"
        "- Add students one by one or **import a CSV** (you see a preview first).\n"
        "- Tick **family consent** when the form comes back. Students without consent are listed on your dashboard.",
        30,
    ),
    "licence-and-payments": (
        "Licence, Level Packs and payments",
        ADMINS,
        "licensing:my_licence,licensing:licence_list,payments:upload,payments:payment_list,payments:payment_detail",
        "Plans, Level Packs, and paying by bank transfer with a payslip.",
        "1. Open **Pay by bank transfer** and check the price (GST 15 % is added).\n"
        "2. Pay at your bank using the reference shown.\n"
        "3. Upload the payslip (PDF, JPG or PNG).\n"
        "4. The Super Admin checks it and approves – your plan or Level Pack starts straight away "
        "and you can download a tax receipt.\n\n"
        "Kura and small rural schools can ask for the 50 % community discount.",
        31,
    ),
    "tickets": (
        "Tickets (Tautoko)",
        "super_admin,school_admin,teacher,student",
        "helpdesk:ticket_list,helpdesk:ticket_new,helpdesk:ticket_detail,helpdesk:report_question",
        "Ask for help and follow the answer with a ticket number.",
        "Students' tickets go to their teachers, teachers' tickets go to the School Admin, and School Admin "
        "tickets go to the CyberQuest team.\n\n"
        "- Add up to 3 screenshots (hide passwords first).\n"
        "- Staff can add **internal notes** that the student cannot see.\n"
        "- Target times: urgent 4 hours, high 1 day, normal 3 days, low 5 days.",
        40,
    ),
    "two-step-login": (
        "Two-step login (MFA)",
        "super_admin,school_admin,teacher",
        "accounts:mfa_setup,accounts:mfa_verify",
        "Protect your account with a 6-digit code from an authenticator app.",
        "Scan the QR code with Google Authenticator, Microsoft Authenticator or similar, then type the code.\n\n"
        "Keep the backup codes somewhere safe. The Super Admin can switch two-step login on or off for any user.",
        41,
    ),
    "users-and-login-as": (
        "Users, Login as and demo accounts",
        "super_admin",
        "accounts:user_list,accounts:user_edit,accounts:user_new,accounts:demo_accounts,"
        "accounts:login_as,accounts:user_security",
        "Manage every account, and see the app exactly as another user sees it.",
        "**Login as** opens another user's dashboard for testing. A yellow bar shows who you are viewing as; "
        "press **Return to Super Admin** to go back. Every Login as is written to the security log.\n\n"
        "**Demo accounts** lists the test logins (demo mode only). Real users' passwords are never shown.",
        50,
    ),
    "system": (
        "System, settings and backups",
        "super_admin",
        "core:system,core:settings,core:settings_review,core:audit_log,core:super_dashboard",
        "Health check, backups, feature switches, settings and the audit log.",
        "- Changing a setting shows the **old and new value** first and asks you to confirm.\n"
        "- **Backups** copy the database; restoring needs you to type RESTORE.\n"
        "- **Feature switches** turn parts of the app on or off (AI helper, WhatsApp, maps…).\n"
        "- `/health/` is used by Docker to check the app is running.",
        51,
    ),
    "security-log": (
        "Security log",
        "super_admin",
        "security:log",
        "Logins, failed logins, lockouts, Login as, MFA changes, rejected uploads and API key changes.",
        "After 5 wrong passwords an account is locked for 15 minutes. Filter by event or user, or export CSV "
        "for an audit.",
        52,
    ),
    "integrations": (
        "Integrations and API keys",
        "super_admin",
        "integrations:list,integrations:ai_test",
        "Connect Gmail, AI services, Google Maps, WhatsApp and Viber.",
        "Paste the key and press **Save**, then **Test connection**. Keys are encrypted and only shown masked.\n\n"
        "- **Gmail** needs an App Password (Google Account → Security → App passwords).\n"
        "- **AI** answers are drafts only. Without a key the offline helper is used.\n"
        "- WhatsApp and Viber business messages cost money and need parents to opt in. Free share buttons need no key.",
        53,
    ),
    "emails": (
        "Emails and templates",
        ADMINS,
        "emails:template_list,emails:template_edit,emails:bulk,emails:log",
        "Automatic emails, editable templates and bulk email to whānau or teachers.",
        "Templates use placeholders like {name} and {school}. Bulk email shows how many people will get it before "
        "sending. Parents only get emails if the family opted in, and every bulk email has an unsubscribe link.",
        54,
    ),
    "media": (
        "Images, audio, video and YouTube",
        STAFF,
        "medialib:media_list,medialib:upload,medialib:video_add",
        "Add pictures, sound and videos to topics.",
        "Uploads are checked for their real file type and size (image 5 MB, audio 20 MB, video 100 MB by default). "
        "YouTube videos play from the privacy-enhanced youtube-nocookie.com link.\n\n"
        "The Cultural Guide ticks **culturally checked** before media with Māori content is published.",
        55,
    ),
    "ai-drafts": (
        "AI drafts and the two approvals",
        "super_admin,teacher",
        "ai_assistant:draft_list,ai_assistant:draft_new,ai_assistant:draft_detail",
        "AI can suggest questions and tips. People always decide.",
        "1. Ask for a draft (question, safety tip or explanation).\n2. A **teacher** checks the facts and approves.\n"
        "3. The **Cultural Guide (Kaiārahi)** checks the wording is culturally safe.\n"
        "4. Only then can it be published. Never type student names into the AI box.",
        56,
    ),
    "announcements": (
        "Announcements (Pānui)",
        "super_admin,school_admin,teacher,student",
        "announcements:list,announcements:new",
        "Short notices shown on dashboards.",
        "The Super Admin can send to every school; a School Admin sends to their own school. Choose who sees it "
        "and the dates it shows.",
        57,
    ),
    "guest": (
        "Demo Guest",
        "guest",
        "website:guest_tour,quizzes:guest_try",
        "Look around safely – the demo guest cannot change anything.",
        "Try a short quiz and visit the tour. To see the full app, ask the presenter to use Login as.",
        60,
    ),
}

# role: [(step title, URL name, what to do)]
TOURS = {
    "super_admin": [
        ("Check the system is healthy", "core:system", "Green ticks mean the database, files and email are fine."),
        ("Look at business intelligence", "reports:bi_dashboard", "Schools, income, exams and tickets."),
        ("Review payslips", "payments:payment_list", "Approve or reject waiting payments."),
        ("Answer tickets", "helpdesk:ticket_list", "Website and School Admin tickets come to you."),
        ("Try Login as", "accounts:user_list", "Open a teacher's dashboard to see what they see."),
        ("Connect services", "integrations:list", "Add the Gmail App Password and an AI key when ready."),
    ],
    "school_admin": [
        ("Make classes and sections", "schools:class_list", "For example Year 7 with sections 7A and 7B."),
        ("Add students", "schools:student_list", "One by one or with a CSV import."),
        ("Check your licence", "licensing:my_licence", "See your plan, Level Packs and the end date."),
        ("See school reports", "reports:school_bi", "Results by section and weakest categories."),
    ],
    "teacher": [
        ("Assign the Level 1 exam", "quizzes:assignment_list", "Pick a section and press Assign."),
        ("Open a class report", "reports:class_report_pick", "Download CSV or PDF."),
        ("Write a practice question", "learning:question_new", "Add clear feedback that teaches the safe choice."),
        ("Try the AI helper", "ai_assistant:draft_new", "Ask for a draft question – you approve it first."),
    ],
    "student": [
        ("Open your levels", "quizzes:student_dashboard", "Start with the first open level."),
        ("Practise a topic", "quizzes:student_dashboard", "Feedback comes after every answer."),
        ("See your results", "quizzes:my_results", "Scores and badges."),
        ("Get your certificate", "certificates:my_certificates", "Pass an exam to get one."),
    ],
    "guest": [
        ("Take the tour", "website:guest_tour", "See what each role can do."),
        ("Try a quiz", "quizzes:guest_try", "Five quick questions."),
    ],
}
