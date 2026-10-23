"""
feedback.py - Kind messages for answers and results (never "Fail")
==================================================================

Owner: Anish Shrestha (task A-15). Words checked by the Māori liaison team (simulated).
"""
from __future__ import annotations

import random

CORRECT = [
    "Well done! (Ka pai!) 🎉 You spotted the trick.",
    "Ka pai! (Well done!) ✅ That is the safe choice.",
    "Awesome! 🌟 You're thinking like a Cyber Guardian.",
    "Tino pai! (Very good!) 👏 Keep it up.",
]

WRONG = [
    "Good try! Mistakes help us learn. 💡 Here's why…",
    "Not quite – that's okay! 🌱 Let's look at the safe choice.",
    "Nice effort! Every expert started as a beginner. 💡",
]

HALFWAY = "Keep going, you're doing great! (Kia kaha!) 💪"
SAFETY_REMINDER = ("If something online feels wrong, talk to a trusted adult – a teacher or family "
                   "member (whānau). 🤝 Netsafe can help too.")
TIPS = [
    "Use a long passphrase like Kiwi-Tui-Rain-42! instead of a short password.",
    "Stop and think before you click a link in a message.",
    "Never share a one-time code, even with a friend.",
    "Check the sender's real email address, not just the name.",
    "Turn on two-step verification (MFA) for your important accounts.",
    "Keep your apps and devices updated – updates fix security holes.",
    "Use your own charger and a power socket instead of public USB ports.",
    "Never paste private information about people into an AI chatbot.",
    "Ask before you post a photo of someone else.",
    "If a deal sounds too good to be true, it probably is a scam.",
]


class FeedbackService:
    """Chooses friendly messages for answers and results."""

    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def answer_message(self, is_correct: bool) -> str:
        return self.rng.choice(CORRECT if is_correct else WRONG)

    @staticmethod
    def halfway_message() -> str:
        return HALFWAY

    @staticmethod
    def safety_reminder() -> str:
        return SAFETY_REMINDER

    def tip_of_the_day(self) -> str:
        return self.rng.choice(TIPS)

    @staticmethod
    def result_message(percentage: float, passed: bool, is_exam: bool) -> str:
        """Headline shown at the end of a quiz or exam."""
        if is_exam and passed and percentage >= 90:
            return "Level complete! 🏆 Outstanding work – you're becoming a Cyber Guardian."
        if is_exam and passed:
            return "Level complete! 🎉 Ka pai – you passed this level exam."
        if percentage >= 75:
            return "Great work! 🌟 You know a lot about staying safe online."
        if percentage >= 50:
            return "Good effort! 💪 Review the topics below and you'll get there – kia kaha!"
        return "Every expert started as a beginner. 🌱 Review these topics and try again."
