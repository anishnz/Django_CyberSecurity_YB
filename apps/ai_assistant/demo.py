"""demo.py - Demo AI drafts in each approval state (offline helper text). Owner: Jihe Qi (test data)."""

from django.contrib.auth import get_user_model

from apps.learning.models import LearningTopic

from .models import AIDraft

User = get_user_model()


def load_demo_drafts() -> int:
    """Three demo drafts: waiting, waiting for the Kaiārahi, and approved."""
    sione, jane = User.objects.get(username="sione.faleolo"), User.objects.get(username="jane.wilson")
    topic = (
        LearningTopic.objects.filter(category="PHISH").order_by("level__number").first()
        or LearningTopic.objects.first()
    )
    common = {"created_by": sione, "school": sione.school, "provider": "Offline helper (no AI key)", "topic": topic}
    AIDraft.objects.create(
        kind=AIDraft.QUESTION,
        request_text="fake prize messages on gaming apps",
        text=(
            "Question: A message in your game says you won 10,000 free coins. "
            "It asks for your password. What should you do?\n"
            "A: Type your password quickly\nB: Do not reply, and tell a trusted adult\nC: Send it to your friends\n"
            "D: Click the link to check\nAnswer: B\n"
            "Feedback: Real games never ask for your password. Stop, and tell a trusted adult."
        ),
        **common
    )
    AIDraft.objects.create(
        kind=AIDraft.PARENT,
        request_text="phishing week message for whānau",
        text=(
            "Kia ora whānau,\n\nThis week our ākonga are learning to spot fake messages. "
            "Ask your child to show you one trick "
            "scammers use, and talk about who they can tell if something feels wrong online."
        ),
        needs_cultural_check=True,
        teacher_approved_by=sione,
        **common
    )
    AIDraft.objects.create(
        kind=AIDraft.TIP,
        request_text="strong passphrases",
        text=("Use a passphrase: three or four random words joined together are easy to remember and hard to guess."),
        teacher_approved_by=jane,
        status=AIDraft.APPROVED,
        **common
    )
    return 3
