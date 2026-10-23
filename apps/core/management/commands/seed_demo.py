"""
seed_demo - Install reference data and the demo schools, users and results
==========================================================================

Owner: Rajneesh Kumar (task R-17)

Usage:
    python manage.py seed_demo            # first install (skips if demo data exists)
    python manage.py seed_demo --reset    # delete demo schools/users and load them again

All names are made up. The same four schools as the Flask version:
    Bright Star School (Te Kura o Whetū Mārama)  BASIC, ends in 10 days, packs L2 L3
    Kathmandu Valley Demo School                  STANDARD, pack L2 (sample school 1)
    Tui Valley School                             BASIC, expired 40 days ago
    Kauri Coast Kura                              TRIAL with 50% community discount
"""
from __future__ import annotations

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.clock import today
from apps.core.models import FeatureSwitch, SystemSettings
from apps.core.services import AuditService
from apps.learning.importer import ContentImporter
from apps.learning.models import AnswerOption, Level, Question
from apps.licensing.keys import LicenseKeyValidator
from apps.licensing.models import License, LevelPack
from apps.schools.models import School, SchoolClass, Section

User = get_user_model()

SUPER_ADMIN = ("superadmin", "Everest@2026", "Anish", "Shrestha")
PASSWORDS = {"school_admin": "Admin@2026", "teacher": "Teacher@2026", "student_nz": "Kiaora@2026",
             "student_np": "Namaste@2026", "guest": "Guest@2026"}
FILLER_FIRST = ["Aiden", "Aroha", "Ben", "Chloe", "Daniel", "Eru", "Fetu", "Grace", "Hamish", "Ihaia", "Jasmine",
                "Kahu", "Lily", "Mason", "Nikau", "Olivia", "Paora", "Quinn", "Rangi", "Sophie", "Tane", "Una", "Vai",
                "William", "Xavier", "Yuki", "Zara", "Ana", "Bodhi", "Cooper", "Daisy", "Eli", "Freya", "George", "Hine"]
FILLER_LAST = ["Brown", "Ngata", "Wilson", "Lee", "Kumar", "Walker", "Tuilagi", "Harris", "Campbell", "Ruru"]
SWITCHES = [("ai", "AI helper", "Short AI text drafts (always reviewed by a person)."),
            ("whatsapp", "WhatsApp messages", "Send messages to opted-in parents."),
            ("viber", "Viber messages", "Send messages to opted-in parents."),
            ("maps", "Google Maps", "Show school locations."),
            ("youtube", "YouTube videos", "Show YouTube videos on topic pages."),
            ("leaderboard", "Class leaderboard", "First names only; teacher must turn it on."),
            ("email_auto_reply", "Email auto-reply", "Reply to support emails and open a ticket.")]


class Command(BaseCommand):
    help = "Load reference data and demo data (use --reset to reload demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo schools and users first.")
        parser.add_argument("--no-demo", action="store_true", help="Only reference data and the Super Admin.")

    def handle(self, *args, **opts):
        self.validator = LicenseKeyValidator()  # pylint: disable=attribute-defined-outside-init
        self.hash_cache = {}  # pylint: disable=attribute-defined-outside-init
        SystemSettings.load()
        for key, label, desc in SWITCHES:
            FeatureSwitch.objects.get_or_create(key=key, defaults={"label": label, "description": desc,
                                                                   "enabled": key not in ("leaderboard",)})
        content = ContentImporter().import_all()
        self._reference_extras()
        self._super_admin()
        if opts["no_demo"]:
            self.stdout.write(self.style.SUCCESS(f"Reference data ready: {content}"))
            return
        if opts["reset"]:
            self._delete_demo()
        elif School.objects.filter(is_demo=True).exists():
            self.stdout.write("Demo data already loaded (use --reset to reload).")
            return
        summary = self._demo()
        AuditService.log(None, "demo_loaded", details=str(summary))
        self.stdout.write(self.style.SUCCESS(f"Demo data loaded: {content} {summary}"))

    # ----------------------------------------------------------- helpers
    @staticmethod
    def _reference_extras():
        """Default email templates and help articles (Sprint 3 onward)."""
        # pylint: disable=import-outside-toplevel
        from apps.emails.services import EmailService
        from apps.helpcentre.services import HelpService
        EmailService.ensure_defaults()
        HelpService.ensure_defaults()

    def _super_admin(self):
        username, password, first, last = SUPER_ADMIN
        if not User.objects.filter(username=username).exists():
            user = User(username=username, first_name=first, last_name=last, role="super_admin",
                        email="superadmin@cyberquest.local", is_staff=True, is_superuser=True, is_demo=True,
                        demo_password=password)
            user.set_password(password)
            user.save()

    @staticmethod
    def _delete_demo():
        from apps.announcements.models import Announcement  # pylint: disable=import-outside-toplevel
        Announcement.objects.filter(school__isnull=True, created_by__is_demo=True).delete()
        User.objects.filter(is_demo=True).exclude(role="super_admin").delete()
        School.objects.filter(is_demo=True).delete()

    def _password(self, user, password, reuse=False):
        """Hash once and reuse for filler students so loading is fast."""
        if reuse and password in self.hash_cache:
            user.password = self.hash_cache[password]
        else:
            user.set_password(password)
            self.hash_cache[password] = user.password

    def _school(self, code, name, region, plan, start, expiry, discount=False, packs=(), **extra):
        school = School.objects.create(code=code, name=name, region=region, is_demo=True, **extra)
        License.objects.create(school=school, plan=plan, start_date=start, expiry_date=expiry,
                               community_discount=discount, product_key=self.validator.generate(code, plan, expiry))
        for level in packs:
            exp = today() + timedelta(days=365)
            LevelPack.objects.create(school=school, level=level, expiry_date=exp,
                                     product_key=self.validator.generate(code, f"L{level}", exp))
        return school

    def _user(self, school, role, username, first, last, password_key, reuse=False, **extra):
        user = User(username=username, first_name=first, last_name=last, role=role, school=school, is_demo=True,
                    email=f"{username}@demo.cyberquest.local", demo_password="" if reuse else PASSWORDS[password_key],
                    **extra)
        self._password(user, PASSWORDS[password_key], reuse)
        user.save()
        return user

    def _sections(self, school, class_name, year, names):
        cls = SchoolClass.objects.create(school=school, name=class_name, year_level=year)
        return {n: Section.objects.create(school_class=cls, name=n, capacity=35) for n in names}

    def _students(self, school, section, names, pkey, missing=(), reuse=False):
        made = {}
        for first, last in names:
            username = f"{first}.{last}".lower().replace(" ", "").replace("'", "")
            user = self._user(school, "student", username, first, last, pkey, reuse=reuse)
            profile = user.student_profile          # created by the accounts post_save signal
            profile.section, profile.family_consent = section, first not in missing
            profile.parent_name, profile.parent_opt_in = f"{last} whānau", True
            profile.parent_email = f"parent.{username}@demo.cyberquest.local"
            profile.save()
            made[first] = user
        return made

    # -------------------------------------------------------------- demo
    @transaction.atomic
    def _demo(self) -> dict:
        d = today()
        bright = self._school("BRIGHTSTAR", "Bright Star School (Te Kura o Whetū Mārama)", "northland", "BASIC",
                              d - timedelta(days=355), d + timedelta(days=10), packs=(2, 3),
                              address="12 Kauri Road, Whangārei 0110", latitude=-35.725200, longitude=174.323700)
        self._user(bright, "school_admin", "admin.brightstar", "Aroha", "Tipene", "school_admin")
        sione = self._user(bright, "teacher", "sione.faleolo", "Sione", "Faleolo", "teacher")
        jane = self._user(bright, "teacher", "jane.wilson", "Jane", "Wilson", "teacher")
        jane.is_cultural_guide = True          # demo Cultural Guide (Kaiārahi) for AI drafts and media
        jane.save(update_fields=["is_cultural_guide"])
        y7 = self._sections(bright, "Year 7", 7, ["7A", "7B", "7C"])
        y8 = self._sections(bright, "Year 8", 8, ["8A"])
        s7a = self._students(bright, y7["7A"], [("Tama", "Ngata"), ("Aria", "Smith"), ("Wiremu", "Tipoki"),
                             ("Losa", "Fifita"), ("Aashish", "Patel"), ("Sita", "Gurung"), ("Jack", "Thompson"),
                             ("Manaia", "Rewi")], "student_nz")
        self._students(bright, y7["7B"], [("Ruby", "Chen"), ("Hana", "Kingi"), ("Leo", "Martin"), ("Mia", "Wong"),
                       ("Noah", "Brown"), ("Anahera", "Hohaia")], "student_nz", missing=("Ruby",))
        filler = [(FILLER_FIRST[i], FILLER_LAST[i % len(FILLER_LAST)]) for i in range(35)]
        self._students(bright, y7["7C"], filler, "student_nz", reuse=True)
        s8a = self._students(bright, y8["8A"], [("Ella", "Johnson"), ("Ravi", "Singh"), ("Moana", "Pene"),
                             ("Sam", "Taylor"), ("Isla", "Clarke")], "student_nz")
        self._user(None, "guest", "demo_guest", "Demo", "Guest", "guest")

        ktm = self._school("KTMVALLEY", "Kathmandu Valley Demo School", "other", "STANDARD",
                           d - timedelta(days=60), d + timedelta(days=305), packs=(2,), address="Kathmandu, Nepal (demo)")
        self._user(ktm, "school_admin", "admin.ktm", "Ram", "Adhikari", "school_admin")
        sita = self._user(ktm, "teacher", "sita.sharma", "Sita", "Sharma", "teacher")
        c7 = self._sections(ktm, "Class 7", 7, ["Everest", "Annapurna"])
        everest = self._students(ktm, c7["Everest"], [("Bikash", "Thapa"), ("Pooja", "Shrestha"), ("Suman", "Rai"),
                                 ("Anjali", "Gurung"), ("Rojan", "Maharjan")], "student_np")
        self._students(ktm, c7["Annapurna"], [("Sujata", "Karki"), ("Prakash", "Tamang"), ("Nisha", "Basnet")], "student_np")

        tui = self._school("TUIVALLEY", "Tui Valley School", "northland", "BASIC",
                           d - timedelta(days=405), d - timedelta(days=40))
        self._user(tui, "school_admin", "admin.tuivalley", "Grace", "Morgan", "school_admin")
        tv = self._sections(tui, "Year 7", 7, ["7T"])
        self._students(tui, tv["7T"], [("Kauri", "Wells"), ("Pania", "Moore")], "student_nz")

        kauri = self._school("KAURICOAST", "Kauri Coast Kura", "northland", "TRIAL",
                             d - timedelta(days=5), d + timedelta(days=25), discount=True)
        self._user(kauri, "school_admin", "admin.kauricoast", "Rawiri", "Pomare", "school_admin")

        q = Question.objects.create(level=Level.objects.get(number=1), category="PRIV", q_type="single",
                                    topic_code="L1-T4", text="Someone you don't know asks for the school Wi-Fi password "
                                    "at the school gate. What should you do?",
                                    feedback="Only staff give out network details. Politely say no and tell a teacher.",
                                    created_by=sione, school=bright)
        for label, text, ok in (("A", "Tell them – it is only Wi-Fi", False), ("B", "Say no and tell a teacher", True),
                                ("C", "Write it on a piece of paper for them", False)):
            AnswerOption.objects.create(question=q, label=label, text=text, is_correct=ok)

        people = {"sione": sione, "jane": jane, "sita": sita, "s7a": s7a, "s8a": s8a, "everest": everest,
                  "y7": y7, "y8": y8, "c7": c7}
        exams = self._activity(people)
        tickets = self._tickets(people)
        extras = self._sprint4_demo()
        return {"demo_schools": 4, "users": User.objects.filter(is_demo=True).count(), "demo_exams": exams,
                "demo_tickets": tickets, **extras}

    @staticmethod
    def _sprint4_demo() -> dict:
        """Payments, announcements, AI drafts and media (Sprint 4)."""
        # pylint: disable=import-outside-toplevel
        from apps.announcements.demo import load_demo_announcements
        from apps.payments.demo import load_demo_payments
        out = {"demo_payments": load_demo_payments(), "demo_announcements": load_demo_announcements()}
        try:
            from apps.ai_assistant.demo import load_demo_drafts
            out["demo_ai_drafts"] = load_demo_drafts()
        except ImportError:
            pass
        return out

    @staticmethod
    def _tickets(people) -> int:
        """Demo help desk tickets (Sprint 3 onward)."""
        try:
            from apps.helpdesk.demo import load_demo_tickets  # pylint: disable=import-outside-toplevel
        except ImportError:
            return 0
        return load_demo_tickets(people)

    @staticmethod
    def _activity(people) -> int:
        """Assignments, exams and practice through the real quiz engine (Sprint 2 onward)."""
        try:
            from apps.quizzes.demo import load_demo_activity  # pylint: disable=import-outside-toplevel
        except ImportError:
            return 0
        return load_demo_activity(people, random.Random(2026))
