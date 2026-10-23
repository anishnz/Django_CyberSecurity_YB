"""
categories.py - Question categories and which categories each level uses
=======================================================================

Owner: Anish Shrestha (task A-11); content by Jihe Qi with the Māori liaison team.
Dictionaries as lookup tables keep the rules in one place (no long if/else).
Every level exam = 4 categories × 5 questions × 5 marks = 100 marks.
"""

from __future__ import annotations

# Code -> (name, Bootstrap icon)
CATEGORIES = {
    "CB": ("Cyber basics", "shield-check"),
    "ETH": ("Digital ethics, IT ethics and intellectual property", "people"),
    "PWD": ("Passwords and account security", "key"),
    "PRIV": ("Personal information, privacy and digital footprint", "person-lock"),
    "PHISH": ("Phishing and scams", "envelope-exclamation"),
    "SPOOF": ("Email spoofing and fake websites", "globe2"),
    "SOC": ("Social engineering", "chat-dots"),
    "DEV": ("Device safety: chargers, Wi-Fi, mobile and IoT", "phone"),
    "WEB": ("Web tricks and web security", "window-stack"),
    "SEC": ("Security principles and models", "diagram-3"),
    "ACC": ("Access control", "door-closed"),
    "AI": ("AI and LLM safety", "robot"),
    "LAW": ("New Zealand cyber law", "bank"),
    "ATK": ("Cyberattacks and attackers", "bug"),
    "FOR": ("Digital forensics", "search"),
}

# Each level exam uses exactly these four categories (5 questions each).
LEVEL_CATEGORIES = {
    1: ["CB", "ETH", "PWD", "PRIV"],
    2: ["PHISH", "SPOOF", "PRIV", "PWD"],
    3: ["SOC", "DEV", "WEB", "ETH"],
    4: ["SEC", "ACC", "AI", "LAW"],
    5: ["SEC", "ATK", "SOC", "ETH"],
    6: ["FOR", "WEB", "AI", "LAW"],
}

# Category names can be more specific at a given level.
LEVEL_CATEGORY_NAMES = {
    (1, "ETH"): "Digital ethics",
    (1, "PRIV"): "Personal information and help",
    (2, "PRIV"): "Privacy and digital footprint",
    (2, "PWD"): "Account security",
    (3, "ETH"): "IT ethics and intellectual property",
    (3, "WEB"): "Web tricks",
    (4, "SEC"): "Security principles (CIA and threats)",
    (4, "LAW"): "NZ cyber law basics",
    (5, "SEC"): "Security policies and models",
    (5, "SOC"): "Social engineering and cyber terrorism",
    (5, "ETH"): "Ethics, IP and NZ law",
    (6, "WEB"): "Web application security",
    (6, "AI"): "AI/LLM security",
    (6, "LAW"): "Security management and law",
}


def category_name(code: str, level: int | None = None) -> str:
    """Return a friendly category name, e.g. 'PWD' -> 'Passwords and account security'."""
    if level is not None and (level, code) in LEVEL_CATEGORY_NAMES:
        return LEVEL_CATEGORY_NAMES[(level, code)]
    return CATEGORIES.get(code, (code, "tag"))[0]


def category_icon(code: str) -> str:
    """Bootstrap icon name for a category."""
    return CATEGORIES.get(code, (code, "tag"))[1]


CATEGORY_CHOICES = [(code, name) for code, (name, _icon) in CATEGORIES.items()]
