"""
labels.py - English (Māori) labels used across the screens
==========================================================

Owner: Dinesh Upreti (task D-03). Words checked by the Māori liaison team
(Kiri Rāwiri, Hēmi Te Awa - simulated). Rule: English first, Māori in brackets.
"""
LABELS = {
    "login": ("Login", "Takiuru"), "logout": ("Logout", "Takiputa"), "password": ("Password", "Kupuhipa"),
    "welcome": ("Welcome", "Nau mai"), "hello": ("Hello", "Kia ora"), "dashboard": ("Dashboard", "Papatohu"),
    "teacher": ("Teacher", "Kaiako"), "student": ("Student", "Ākonga"), "principal": ("Principal", "Tumuaki"),
    "family": ("Family", "Whānau"), "class": ("Class", "Akomanga"), "settings": ("Settings", "Tautuhinga"),
    "report": ("Report", "Pūrongo"), "notices": ("Notices", "Pānui"), "learn": ("Learn", "Ako"),
    "school": ("School", "Kura"), "help": ("Help", "Āwhina"), "well_done": ("Well done!", "Ka pai!"),
    "keep_going": ("Keep going!", "Kia kaha!"), "thank_you": ("Thank you", "Ngā mihi"),
    "support": ("Support", "Tautoko"), "certificate": ("Certificate", "Tiwhikete"), "email": ("Email", "Īmēra"),
    "community": ("Community", "Hapori"), "about": ("About us", "Mō mātou"), "contact": ("Contact us", "Whakapā mai"),
    "home": ("Home", "Kāinga"), "levels": ("Levels", "Taumata"), "guide": ("Guide", "Kaiārahi"),
}


def label(key: str, english_only: bool = False) -> str:
    """'dashboard' -> 'Dashboard (Papatohu)'."""
    english, maori = LABELS.get(key, (key.replace("_", " ").capitalize(), ""))
    return english if english_only or not maori else f"{english} ({maori})"
