"""
business.py - Business pages: proposal, sustainability, comparison, SWOT, contract, discounts
============================================================================================

Owner: Dinesh Upreti (Business Analyst, task D-15); prices and contract with Rajneesh Kumar (task R-14)

All money is in New Zealand dollars. Prices come from the Plan classes in
``apps.licensing.plans`` so the website can never show a different price from
the app. Running costs are planning estimates for the simulated company.

Concepts:
    * Encapsulation: ``SustainabilityModel`` keeps the cost list and the maths
      together; templates only read its results.
    * Polymorphism: ``price_table()`` asks every Plan object for its own
      ``monthly_price()``, with and without the community discount.
    * Dataclasses: ``CostLine`` and ``Scenario`` are small value objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from apps.licensing.plans import LEVEL_PACK_PRICES, PLAN_CLASSES

GST = Decimal("0.15")
CENT = Decimal("0.01")
BUILD_COST = Decimal("33420.17")  # Project Report: total cost excluding GST
BUILD_COST_GST = Decimal("38433.20")


def money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


# =============================================================================== prices and discounts
def price_table() -> list[dict]:
    """One row per plan: monthly, yearly (excl. and incl. GST) and the community price."""
    rows = []
    for cls in PLAN_CLASSES.values():
        normal, community = cls(None, None), cls(None, None, community_discount=True)
        yearly = normal.monthly_price() * 12
        rows.append(
            {
                "name": cls.DISPLAY_NAME,
                "code": cls.CODE,
                "sections": normal.section_limit_label,
                "monthly": money(normal.monthly_price()),
                "yearly": money(yearly),
                "yearly_gst": money(yearly * (1 + GST)),
                "community_monthly": money(community.monthly_price()),
                "community_yearly_gst": money(community.monthly_price() * 12 * (1 + GST)),
            }
        )
    return rows


def level_pack_total() -> Decimal:
    """Price of all Level Packs (Levels 2–6) for one year."""
    return sum(LEVEL_PACK_PRICES.values(), Decimal("0"))


DISCOUNT_STEPS = [
    (
        "Start with the free trial",
        "Every new school gets a free 30-day trial with one class section. Level 1 is always free.",
    ),
    (
        "Ask for the community discount",
        "Use Contact us and choose 'Community and kura partnership'. Tell us the school name and that it is a kura "
        "or a small rural school.",
    ),
    (
        "We check and switch it on",
        "Our Super Admin checks the school and turns on the 50% community discount on the school's licence. "
        "Every change is written to the audit log.",
    ),
    (
        "Pay the lower price",
        "Your next invoice shows the plan at half price. Pay by bank transfer and upload the payslip in the app.",
    ),
]

DISCOUNT_FAQ = [
    ("Who can get the 50% discount?", "Kura (Māori-medium schools) and small rural schools."),
    (
        "What does it cover?",
        "The monthly plan price (Basic, Standard or Unlimited). Level Packs keep their normal price.",
    ),
    ("Do students ever pay?", "No. Only the school pays. Students never see prices or payment screens."),
    (
        "Can a group of schools ask for a better price?",
        "Yes. A school group can ask for a group agreement. The price is written into the contract.",
    ),
]


# =============================================================================== sustainability
@dataclass(frozen=True)
class CostLine:
    """One yearly running cost (planning estimate)."""

    item: str
    note: str
    amount: Decimal


@dataclass(frozen=True)
class Scenario:
    """A mix of schools, and how many schools are needed to cover the yearly target."""

    name: str
    community_share: Decimal  # 0.3 = 30% of schools get the community discount
    income_per_school: Decimal
    schools_needed: int


class SustainabilityModel:
    """How many paying schools CyberQuest needs to pay its own way every year."""

    def __init__(self, costs: list[CostLine], build_cost: Decimal = BUILD_COST, payback_years: int = 3):
        self.costs = costs
        self.build_cost = build_cost
        self.payback_years = payback_years
        self.contingency_rate = Decimal("0.10")

    @property
    def running_subtotal(self) -> Decimal:
        return money(sum((c.amount for c in self.costs), Decimal("0")))

    @property
    def contingency(self) -> Decimal:
        return money(self.running_subtotal * self.contingency_rate)

    @property
    def running_total(self) -> Decimal:
        return self.running_subtotal + self.contingency

    @property
    def payback_per_year(self) -> Decimal:
        """Part of the build cost paid back each year."""
        return money(self.build_cost / self.payback_years)

    @property
    def yearly_target(self) -> Decimal:
        return self.running_total + self.payback_per_year

    @staticmethod
    def income_per_school(plan_code: str = "STANDARD", packs: tuple[int, ...] = (2, 3, 4), community=False) -> Decimal:
        """Yearly income (excl. GST) from one school with one plan and some Level Packs."""
        plan = PLAN_CLASSES[plan_code](None, None, community_discount=community)
        return money(plan.monthly_price() * 12 + sum((LEVEL_PACK_PRICES[p] for p in packs), Decimal("0")))

    @property
    def income_per_school_community(self) -> Decimal:
        """The same school with the 50% community discount."""
        return self.income_per_school(community=True)

    def scenario(self, name: str, community_share: Decimal) -> Scenario:
        normal = self.income_per_school()
        community = self.income_per_school(community=True)
        average = money(normal * (1 - community_share) + community * community_share)
        return Scenario(name, community_share, average, math.ceil(self.yearly_target / average))

    def scenarios(self) -> list[Scenario]:
        return [
            self.scenario("All schools pay the normal price", Decimal("0")),
            self.scenario("7 in 10 normal, 3 in 10 community discount", Decimal("0.3")),
            self.scenario("Half of the schools get the community discount", Decimal("0.5")),
        ]


RUNNING_COSTS = [
    CostLine("Cloud server for hosted schools", "12 months × NZD 25", Decimal("300")),
    CostLine("Domain name (.nz)", "1 year", Decimal("30")),
    CostLine("Support mailbox", "12 months × NZD 10.60", Decimal("127.20")),
    CostLine("AI test credit (optional)", "12 months × NZD 30; the offline helper is free", Decimal("360")),
    CostLine("Support, updates and new questions", "6 hours a week × 48 weeks × NZD 45", Decimal("12960")),
    CostLine("Kaiārahi content reviews", "4 reviews × 5 hours × NZD 90", Decimal("1800")),
    CostLine("Community testing (Māori liaison)", "2 people × 12 hours × NZD 60", Decimal("1440")),
    CostLine("Insurance and accounting", "Small business estimate", Decimal("1200")),
]

SUSTAIN_WAYS = [
    (
        "Schools pay, not children",
        "Income comes from school plans and Level Packs. Level 1 stays free, so every school can start.",
    ),
    (
        "Low running cost by design",
        "CyberQuest runs on one school computer with free, open-source tools. There is no cost per student and "
        "AI keys are optional.",
    ),
    (
        "Fair prices keep schools with us",
        "The 50% community discount keeps kura and rural schools in the programme, and they help us test new content.",
    ),
    (
        "Reinvest in content",
        "We plan to put 10% of any profit back into new questions, te reo Māori review and free licences for kura.",
    ),
    (
        "Content that stays current",
        "Teachers can add their own practice questions, and the AI helper drafts new ones that a teacher and the "
        "Kaiārahi check. Scams change fast, so the questions must change too.",
    ),
    (
        "Ready to grow",
        "The new JSON API lets a React or mobile app use the same data later, without building a second system.",
    ),
]


# =============================================================================== comparison
COMPARE_COLUMNS = [
    "CyberQuest",
    "Free global online games",
    "General e-learning platform",
    "One-off school talk",
    "Printed worksheets",
]
# value per column: "yes", "partly", "no" or a short text
COMPARE_ROWS = [
    ("Made for New Zealand (Kiwi examples, te reo Māori labels)", ["yes", "no", "partly", "partly", "partly"]),
    ("Works with no internet", ["yes", "no", "no", "yes", "yes"]),
    ("Six levels, from Year 7 to adults", ["yes", "partly", "partly", "no", "partly"]),
    ("Class reports for teachers", ["yes", "partly", "yes", "no", "no"]),
    ("Certificates anyone can check (QR code)", ["yes", "partly", "partly", "no", "no"]),
    ("Māori content checked by a cultural guide (Kaiārahi)", ["yes", "no", "no", "partly", "partly"]),
    ("AI drafts checked by a teacher and the Kaiārahi", ["yes", "no", "partly", "no", "no"]),
    ("Help desk for schools", ["yes", "no", "yes", "no", "no"]),
    ("Learning all year, not one day", ["yes", "yes", "yes", "no", "partly"]),
    (
        "Cost to the school",
        ["Level 1 free; plans from NZD 100 a month", "Free", "Usually per user", "Per visit", "Low"],
    ),
]
COMPARE_POINTS = [
    "Built with our community: English first, with te reo Māori in brackets, and a Kaiārahi checks Māori content.",
    "Works offline on one school computer – important for rural schools with slow internet or strict filters.",
    "Teachers get kind, simple reports. We never use the word 'Fail' and there is no leaderboard that shames children.",
    "AI only writes drafts. A teacher checks the facts and the Kaiārahi checks Māori content. AI never profiles children.",
    "One platform for learning, exams, certificates, help desk, email to whānau and business reports.",
]


# =============================================================================== SWOT
SWOT = {
    "Strengths": [
        "Made in New Zealand, with te reo Māori labels and Kaiārahi checks",
        "Works offline on one school computer",
        "Strong security: two-step login, encrypted keys, security log",
        "Clear OOP design that is easy to extend and test (Pylint 10/10)",
        "Low price, free Level 1 and a 50% community discount",
        "Class reports and a business dashboard",
    ],
    "Weaknesses": [
        "Small, new team and an unknown brand",
        "Questions need regular updates as scams change",
        "Payslip payments are checked by hand, which is slow",
        "AI features need paid keys from outside companies",
        "No mobile app yet",
    ],
    "Opportunities": [
        "More children use devices and apps at a younger age",
        "Rural schools and kura need tools that work offline",
        "Partnerships with community groups and school groups",
        "A React or mobile app can use the new JSON API",
        "Level 6 can also teach whānau and small businesses",
    ],
    "Threats": [
        "Free resources from large global companies",
        "School budgets are tight",
        "A data breach would damage trust quickly",
        "AI companies can change their prices or rules",
        "New laws or rules may need changes to the app",
    ],
}
SWOT_ACTIONS = [
    ("Use strengths to win opportunities", "Offer the offline version and community discount to rural school groups."),
    ("Fix weaknesses with opportunities", "Build a simple mobile app on the JSON API after the pilot."),
    ("Use strengths against threats", "Show our security and privacy design to schools as a reason to trust us."),
    ("Reduce weaknesses and threats", "Keep the offline AI helper as the default, so AI price changes cannot stop us."),
]


# =============================================================================== proposal
PROPOSAL = {
    "summary": (
        "Mount Everest Digital Limited proposes CyberQuest, a cyber-safety and digital-ethics learning platform for "
        "schools in Te Tai Tokerau (Northland). Students learn through short, game-style lessons, practice "
        "questions and exams across six levels. Teachers get kind, simple reports. The platform works offline, "
        "uses English first with te reo Māori in brackets, and is checked by a Kaiārahi (cultural guide)."
    ),
    "problem": [
        "Children use phones, games and smart devices from a young age, often without guidance.",
        "Scams, fake profiles, deepfakes and social engineering target children and their whānau.",
        "Many rural schools have slow internet and strict filters, so online-only tools do not work.",
        "Teachers have little time and few New Zealand resources about cyber safety and ethics.",
    ],
    "objectives": [
        "Deliver a working platform with six levels and at least 120 questions by 8 November 2026.",
        "Let a teacher see a class report in under one minute.",
        "Run fully offline on one school computer, started with one double-click.",
        "Get Kaiārahi approval for all Māori content before students see it.",
        "Pass all 'Must' user stories in acceptance testing with the client.",
    ],
    "scope_in": [
        "Five roles: Super Admin, School Admin, Teacher, Student, Demo Guest",
        "Learning levels, practice, exams, badges and certificates",
        "Schools, classes, licences, Level Packs and payslip payments",
        "Help desk, email to whānau, announcements and help centre",
        "Reports, business dashboard, integrations and AI drafts",
        "Public website and a JSON API for a future React app",
    ],
    "scope_out": [
        "Card payments inside the app",
        "A native mobile app (planned later, using the API)",
        "A full te reo Māori version of every page",
        "Leaderboards (our Kaiārahi advised against them)",
    ],
    "deliverables": [
        "CyberQuest web application (Django), Docker files and run.bat",
        "Automatic tests, Pylint 10/10 and test evidence",
        "README, user guide, Project Report and reflection reports",
        "Release v1.0.0 on GitHub",
    ],
    "timeline": [
        ("Sprint 0", "1–7 Oct 2026", "Kickoff, requirements, Kaiārahi consultation, backlog and design"),
        ("Sprint 1", "8–14 Oct 2026", "Foundation: login, roles, security, schools, public website"),
        ("Sprint 2", "15–21 Oct 2026", "Learning: levels, questions, practice, exams, licences"),
        ("Sprint 3", "22–28 Oct 2026", "Help desk, emails, integrations, reports and BI"),
        ("Sprint 4", "29 Oct – 4 Nov 2026", "Payments, certificates, help centre, AI drafts, media"),
        ("Sprint 5", "5–8 Nov 2026", "Acceptance testing, quality checks and release"),
    ],
    "budget": [
        ("Labour (team, Kaiārahi and liaison)", Decimal("29620.00")),
        ("Tools and services", Decimal("131.20")),
        ("Resources (laptops, data, travel, koha, printing)", Decimal("630.77")),
        ("Contingency (10%)", Decimal("3038.20")),
    ],
    "risks": [
        ("Team member is away", "Pair work and short tasks; everyone can run the tests."),
        ("Scope grows", "MoSCoW priorities; the Product Owner accepts each sprint."),
        ("Cultural content is wrong", "Kaiārahi approval step; Māori content hidden until approved."),
        ("Data or key leak", "Encrypted keys, two-step login, security log, no keys in Git."),
    ],
    "success": [
        "All 'Must' stories accepted by the client",
        "100+ automatic tests passing and coverage of at least 80%",
        "Kaiārahi acceptance checklist passed",
        "A teacher can run a class from start to certificate",
    ],
}


def proposal_total() -> Decimal:
    """Total of the proposal budget lines; it must match the Project Report (BUILD_COST)."""
    return money(sum((amount for _item, amount in PROPOSAL["budget"]), Decimal("0")))


# =============================================================================== contract sample
CONTRACT_PARTIES = [
    ("The Company", "Mount Everest Digital Limited, Auckland, New Zealand (simulated company for this assignment)"),
    ("The Client", "Northland Digital Safety Schools Group, on behalf of its member schools"),
]
CONTRACT_CLAUSES = [
    (
        "Services",
        [
            "The Company provides the CyberQuest learning platform, set-up help, updates and the help desk.",
            "The Company can run CyberQuest on its server, or the school can run it on its own computer (offline).",
        ],
    ),
    (
        "Term",
        [
            "This agreement starts on the Start Date and lasts 12 months.",
            "It renews for another 12 months unless one party gives 30 days' written notice.",
        ],
    ),
    (
        "Fees and payment",
        [
            "Each school pays the monthly price of its chosen plan and any Level Packs, shown in Schedule 1.",
            "Prices are in New Zealand dollars and exclude GST (15%). GST is added on each invoice.",
            "Invoices are paid by bank transfer within 20 days. The school uploads the payslip in the app.",
            "Students are never asked to pay.",
        ],
    ),
    (
        "Community discount",
        [
            "Kura and small rural schools receive 50% off the monthly plan price.",
            "The Company checks each request and records the decision in the audit log.",
        ],
    ),
    (
        "Privacy and student data",
        [
            "Both parties follow the Privacy Act 2020.",
            "The Company keeps only the student data needed: first name, username, class and consent.",
            "Each school owns its data. The Company uses it only to provide the service.",
            "The Company tells the Client without delay about any privacy breach, and helps notify the Privacy "
            "Commissioner when the law requires it.",
        ],
    ),
    (
        "Māori cultural content (taonga)",
        [
            "Māori words, stories and examples are checked and approved by a Kaiārahi before students see them.",
            "Cultural content given by the community stays with the community. The Company may use it only in "
            "CyberQuest and only while this agreement lasts.",
        ],
    ),
    (
        "Use of AI",
        [
            "AI is used only to write drafts. A teacher checks the facts and the Kaiārahi checks Māori content.",
            "AI is never used to profile, score or judge individual children.",
            "Student personal information is not sent to AI services.",
        ],
    ),
    (
        "Intellectual property",
        [
            "The Company owns the CyberQuest software.",
            "Each school owns the practice questions its teachers write and gives the Company a licence to show them "
            "inside that school.",
        ],
    ),
    (
        "Support and service levels",
        [
            "Help desk tickets are answered within 1 school day.",
            "For hosted schools, the Company aims for the service to be available 99% of school hours each month.",
        ],
    ),
    (
        "Liability",
        [
            "Each party's total liability under this agreement is limited to the fees paid in the 12 months before "
            "the claim, except for breach of privacy or confidentiality.",
        ],
    ),
    (
        "Ending the agreement",
        [
            "Either party may end this agreement with 30 days' written notice, or straight away if the other party "
            "seriously breaks it and does not fix it within 14 days.",
            "When it ends, the Company gives each school an export of its data and then deletes it within 30 days.",
        ],
    ),
    (
        "Disputes and law",
        [
            "The parties first try to solve a dispute in good faith, in a hui (meeting).",
            "If that does not work, they use mediation in Auckland before going to court.",
            "New Zealand law applies to this agreement.",
        ],
    ),
]
