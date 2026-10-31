"""
content.py - Words for the landing page: the problem, real NZ facts, NZ law, our solution, features
=================================================================================================

Owner: Dinesh Upreti (Business Analyst, public website)

Kept in one Python file so the text is easy to check, translate and test. Every number has a source link,
and the "what could happen" stories are clearly marked as made-up examples for teaching, not real cases.
"""

from __future__ import annotations

# ------------------------------------------------------------------------------------------- the problem
PROBLEM_INTRO = (
    "Generation Z and Generation Alpha were born into a connected world. Before they can ride a bike they can "
    "unlock a tablet, talk to a smart speaker, play online games with strangers and watch videos on a parent's "
    "phone. At home and at school, the devices are looked after: IT staff patch the Wi-Fi router, update the "
    "firewall and watch the network with monitoring software."
)
PROBLEM_TURN = (
    "But attackers know the easiest door is often not the device – it is the person holding it. Children trust "
    "quickly, want to help, love prizes and rarely know what a scam looks like. A kind voice, a free game reward or "
    "a lolly can open a door that no firewall can close. These tricks are called social engineering: attacking "
    "people's feelings instead of their computers."
)

# (icon, title, story) – made-up stories that show the risk. Not real cases.
STORIES = [
    (
        "door-open",
        "The smart front door",
        "A friendly stranger offers a child chocolate and asks to \"borrow\" the family phone for a moment. The phone "
        "has the smart-lock app. One tap later the front door is unlocked and the house is open.",
    ),
    (
        "credit-card",
        "The prize that needs a photo",
        "A game chat says: \"You won 10,000 free coins! Send a photo of your dad's bank card to claim them.\" The "
        "child only wants the prize. The photo gives a scammer the card number.",
    ),
    (
        "phone",
        "The borrowed work phone",
        "A bank manager gives their work phone to their child to play a game. A \"helper\" in the game asks the child "
        "to install an app for extra lives. The app gives the attacker remote control of the phone – and a way into "
        "the bank's systems.",
    ),
    (
        "person-bounding-box",
        "The video that is not real",
        "A deepfake video shows a classmate saying things they never said. It spreads in a group chat in minutes. "
        "Real-looking does not mean real, and sharing it can cause serious harm.",
    ),
    (
        "chat-heart",
        "The new online \"friend\"",
        "Someone the child met in a game is very kind, sends gifts and slowly asks for the school name, home address "
        "and photos. This is grooming: building trust to get information.",
    ),
    (
        "cpu",
        "The AI that is not fair",
        "An AI tool gives different answers about people because of their name or where they live. AI can be biased, "
        "can make things up and can be used to copy other people's work. Children need to question what AI tells "
        "them.",
    ),
]
STORIES_NOTE = "These are made-up stories for teaching. They show what can happen when children are not prepared."

# IT ethics examples children meet every day.
ETHICS = [
    "Sharing a friend's photo or video without asking first.",
    "Copying an answer from AI or a website and saying it is your own work.",
    "Logging in with someone else's password, even \"just for fun\".",
    "Downloading pirated games, music or films.",
    "Making or sharing a deepfake, meme or edit that embarrasses someone.",
    "Using AI that treats people unfairly, without checking it.",
]

# ------------------------------------------------------------------------------------------ NZ facts
# (big number, what it means, source title, source url) – checked October 2026.
NZ_FACTS = [
    (
        "$1.6 billion",
        "lost by New Zealanders to online threats in 2024 (survey estimate).",
        "NCSC consumer research 2025",
        "https://www.ncsc.govt.nz/news/consumer-behaviour-research-2025",
    ),
    (
        "54%",
        "of adult New Zealanders had an online threat in the six months before the survey.",
        "NCSC consumer research 2025",
        "https://www.ncsc.govt.nz/news/consumer-behaviour-research-2025",
    ),
    (
        "5,995",
        "cyber incidents reported to the NCSC in 2024/25; 4,343 of them by individuals. Scams and phishing were the "
        "most common.",
        "NCSC Cyber Threat Report 2025",
        "https://www.ncsc.govt.nz/insights-and-research/cyber-threat-reports/cyber-threat-report-2025/"
        "incident-reporting-analysis/",
    ),
    (
        "2×",
        "Teens are about twice as likely as adults to be negatively affected by harmful online messages; younger "
        "teens (14–15) are most at risk.",
        "Netsafe and Ministry for Women, 2018",
        "https://resource.netsafe.org.nz/MR-NZ-Teens-and-Digital-Harm-Report-Press-Release.pdf",
    ),
]
FACTS_NOTE = "The real numbers are likely higher: the NCSC says cyber attacks are under-reported."

# ------------------------------------------------------------------------------------------- NZ law
# (law, what it means in simple words, url)
NZ_LAWS = [
    (
        "Harmful Digital Communications Act 2015",
        "Stops online bullying, harassment and sharing intimate images without consent. Netsafe helps people "
        "who are harmed. Posting a harmful message can mean up to 2 years in prison or a fine of up to $50,000.",
        "https://www.legislation.govt.nz/act/public/2015/0063/latest/whole.html",
    ),
    (
        "Crimes Act 1961 (sections 248–252)",
        "Computer crimes. Getting into a computer without permission can mean up to 2 years in prison; doing it "
        "to cheat or steal can mean up to 7 years.",
        "https://www.legislation.govt.nz/act/public/1961/43/en/latest/",
    ),
    (
        "Privacy Act 2020",
        "Organisations – including schools and apps like CyberQuest – must collect only what they need, keep "
        "personal information safe and tell people about serious privacy breaches.",
        "https://www.legislation.govt.nz/act/public/2020/31/en/latest/",
    ),
    (
        "Unsolicited Electronic Messages Act 2007",
        "Commercial emails and texts need the person's consent and an easy way to unsubscribe (spam is illegal).",
        "https://www.legislation.govt.nz/act/public/2007/7/en/latest/",
    ),
    (
        "Copyright Act 1994",
        "Games, music, films, pictures and writing belong to the people who made them. Copying them without "
        "permission breaks the law.",
        "https://www.legislation.govt.nz/act/public/1994/143/en/latest/",
    ),
    (
        "Deepfakes – a law is being proposed",
        "The Deepfake Digital Harm and Exploitation Bill, a member's bill introduced in 2025, would treat sexual "
        "deepfakes made without consent like intimate recordings under the Crimes Act and the Harmful Digital "
        "Communications Act.",
        "https://legislation.govt.nz/bill/members/2025/213/en/latest/",
    ),
]
HELP_LINKS = [
    ("Netsafe – online safety help", "https://netsafe.org.nz/"),
    ("Report a scam or cyber attack – NCSC Own Your Online", "https://www.ownyouronline.govt.nz/"),
]

# --------------------------------------------------------------------------------------- the solution
FIRE_EXIT = (
    "At every school assembly, concert or event, someone first points to the fire exits. Nobody waits for a fire "
    "to learn where the door is. Digital safety needs the same habit: teach it early, teach it often, and teach "
    "it to everyone – before it is too late."
)

ABOUT_US = [
    "CyberQuest is a cyber-security and digital-safety awareness platform for New Zealand schools.",
    "Students learn by playing: short topics, quick practice rounds with kind feedback, and a level exam.",
    "Six levels grow with the learner – from Year 7 to the end of secondary school (Years 11–13), "
    "plus a level for adults and tertiary students.",
    "Questions and examples are written for each age group, with Kiwi and marae examples and te reo Māori labels.",
    "Every level covers both safety (scams, passwords, devices, AI) and IT ethics (privacy, copyright, kindness).",
    "Teachers assign exams and see which topics their class finds hard, so they know what to teach next.",
    "Schools run classes, students and licences in one place; kura and small rural schools get 50% off.",
    "Built with our Māori community advisers and a Cultural Guide (Kaiārahi) who checks Māori content.",
]

AI_HELPS = [
    "Writes draft practice questions for a topic and age group, ready for a teacher to check.",
    "Drafts short safety tips, simple topic explanations and friendly messages to whānau.",
    "Answers \"How do I…?\" questions on every page with the Explain this page helper.",
    "Removes names and email addresses before anything is sent to an AI service.",
    "Never publishes by itself: a teacher approves every draft, and the Kaiārahi approves Māori content.",
    "Works offline too: without an AI key, a simple built-in helper makes the drafts.",
]
AI_LIMIT = (
    "AI does not judge or profile children. Teachers see learning results – such as the topics a class finds "
    "hardest – not guesses about a child's personality or feelings."
)

# ------------------------------------------------------------------------------------------- features
# (icon, group, [features])
FEATURE_GROUPS = [
    (
        "mortarboard",
        "For students (Ākonga)",
        [
            "Six levels from Cyber Starter to Cyber Pro",
            "Short topics with Kiwi examples, YouTube videos and pictures",
            "Practice with instant feedback, level exams, badges",
            "PDF certificates with a QR code anyone can check",
            "Report a question that looks wrong",
        ],
    ),
    (
        "person-badge",
        "For teachers (Kaiako)",
        [
            "Assign level exams to a section with a due date",
            "Write extra practice questions for the school",
            "Class and student reports, CSV and PDF download",
            "Weakest topics of the class shown first",
            "AI drafts, media library and certificate ZIP",
        ],
    ),
    (
        "building",
        "For schools",
        [
            "Classes, sections (35 students each) and CSV import",
            "Family consent tracking and parent emails with unsubscribe",
            "Licence plans, Level Packs and a free 30-day trial",
            "50% community discount for kura and small rural schools",
            "Pay by bank transfer: upload the payslip, get a GST receipt",
        ],
    ),
    (
        "speedometer2",
        "For the CyberQuest team",
        [
            "Business intelligence dashboard: income, plans, exams, tickets",
            "Login as any user to test their dashboard (logged)",
            "Integrations page for AI, Gmail, Google Maps, WhatsApp and Viber",
            "System settings, feature switches, backups and health check",
            "Email templates and bulk email",
        ],
    ),
    (
        "shield-lock",
        "Security and privacy",
        [
            "Five roles with their own permissions",
            "Two-step login (MFA), switched on or off per user by the Super Admin",
            "Account lockout after 5 wrong passwords",
            "Security log, audit log and encrypted API keys",
            "Upload checks by real file type and size limits",
        ],
    ),
    (
        "bell",
        "Help and communication",
        [
            "Notifications on every dashboard",
            "Tickets with numbers, target times and email updates",
            "Announcements (Pānui) for a school or everyone",
            "Help centre and Explain this page on every screen",
            "Dark mode and larger text",
        ],
    ),
]

# ----------------------------------------------------------------------------- architecture (request journey)
REQUEST_STEPS = [
    (
        "Browser",
        "A student, teacher, admin or visitor opens a page. Bootstrap and Chart.js are served from our own "
        "server, so it works in schools with strict internet filters.",
    ),
    (
        "Docker and waitress",
        "run.bat starts a Docker container on a free port. The waitress web server passes the request to Django.",
    ),
    (
        "Middleware",
        "Security headers (no inline scripts), maintenance mode, account status and two-step login are "
        "checked on every request.",
    ),
    (
        "Views and roles",
        "The URL goes to a view. Decorators such as @role_required check the user's role before anything runs.",
    ),
    (
        "Service layer (OOP)",
        "Services hold the rules: quizzes (Strategy), questions (Factory), notices (Observer), "
        "integrations (Adapter), tickets (state machine).",
    ),
    (
        "Database",
        "Django models save data in SQLite (or PostgreSQL). Uploads are stored in the media folder with "
        "safe random names.",
    ),
    (
        "Outside services",
        "Only when switched on: AI (Claude, OpenAI, Gemini), Gmail, Google Maps, WhatsApp and "
        "Viber. Keys are encrypted.",
    ),
    (
        "Logs and health",
        "Security log, audit log, email log and /health/ show what happened and that the system is working.",
    ),
]


# Real photos of our team meetings (shown in the meetings slider until the Super Admin uploads others).
# (file in static/img/meetings/, title, caption, place)
TEAM_MEETING_PHOTOS = [
    (
        "meeting_1.jpg",
        "Planning together at Yoobee",
        "All four of us plan the next sprint together.",
        "Yoobee College, Auckland",
    ),
    (
        "meeting_2.jpg",
        "Working on the code side by side",
        "The team reviews a feature on a laptop.",
        "Yoobee College, Auckland",
    ),
    ("meeting_3.jpg", "Evening video stand-up", "Our regular WhatsApp video call after 8 pm.", "Online, Auckland"),
    ("meeting_4.jpg", "2nd group assignment call", "The four of us on a phone video call.", "Online, Auckland"),
    (
        "meeting_5.jpg",
        "Code review call",
        "The team reviews the code on a video call.",
        "Online, Auckland",
    ),
    (
        "meeting_6.jpg",
        "Demo video review, 29 Oct 2026",
        "The team watches the narrated demo video together on a call.",
        "Online, Auckland",
    ),
]
