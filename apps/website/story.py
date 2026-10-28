"""
story.py - Our project story (a simulated case study) for the public website
============================================================================

Owner: Anish Shrestha (task A-22)

This is the same simulated story as in our Project Report and meeting records.
The client, the school visit, Bright Star School and the Māori advisers are
fictional roles that we wrote for the assignment. The page says this clearly at
the top, so no reader thinks they are real people or a real visit.
"""

from __future__ import annotations

DECLARATION = (
    "This is a simulated case study for our MSE800 assignment. The client, the school visit, Bright Star School "
    "and the Māori advisers are fictional. We wrote them so our design always asks the community first. In a real "
    "project, these would be real people, and they would be paid for their time and knowledge."
)

WHY_ROLES = (
    "We respect Māori culture and Te Tiriti o Waitangi. We could not ask real Māori community members to give unpaid "
    "time to a student assignment, so we created three fictional community friends. They stand for the voices a "
    "real project must include, and every decision they shaped is in the app."
)

# (date, title, where, text) – dates match the simulated meeting records (M01–M21)
CHAPTERS = [
    (
        "1 October 2026",
        "The problem arrives",
        "Kickoff at Yoobee, Auckland, with the client on video",
        "Ms Aroha Tipene from the Northland Digital Safety Schools Group told us that children in her schools meet "
        "scams, fake friends and unsafe apps every week, but teachers have no simple, local way to teach cyber "
        "safety. Kiri Rāwiri joined to make sure whānau were part of the plan from day one.",
    ),
    (
        "3 October 2026",
        "We ask before we build",
        "First Kaiārahi consultation (video call)",
        "Mrs Mere Paora, our Kaiārahi (cultural guide), asked us to write English first with te reo Māori in "
        "brackets, to let her approve Māori content before students see it, and not to build a leaderboard that "
        "could shame children.",
    ),
    (
        "5 October 2026",
        "A day at Bright Star School",
        "Simulated site visit to a fictional school in Northland",
        "Dinesh and Rajneesh travelled north with Ms Tipene and Hēmi Te Awa. In the story, the classroom had one "
        "projector, slow internet and strict filters. We learned that CyberQuest must work offline, look clear on "
        "a projector and use family consent forms.",
    ),
    (
        "6 October 2026",
        "Fair for kura and rural schools",
        "Phone call with Hēmi Te Awa",
        "Hēmi asked how a small kura could pay. Together we agreed a 50% community discount and product keys, so "
        "a school with poor internet can still switch on its licence.",
    ),
    (
        "20 October 2026",
        "Checking our words together",
        "Second Kaiārahi consultation",
        "Mrs Paora reviewed our topics and te reo Māori labels. She asked for three wording changes and approved a "
        "question about a marae group chat.",
    ),
    (
        "3 November 2026",
        "Testing with the community",
        "Third Kaiārahi consultation and acceptance testing",
        "Mrs Paora and Kiri tested the two-approval AI drafts and the media check. Hēmi joined user acceptance "
        "testing on 6 November, and the client signed off release 1.0 on 7 November.",
    ),
]

# (name, role, proposal, what we built)
PROPOSALS = [
    (
        "Mrs Mere Paora",
        "Kaiārahi (cultural guide)",
        "Write English first, with te reo Māori in brackets.",
        "Bilingual labels across the app, for example Teacher (Kaiako) and Student (Ākonga).",
    ),
    (
        "Mrs Mere Paora",
        "Kaiārahi (cultural guide)",
        "Let me approve Māori content before children see it.",
        "A Kaiārahi approval step. Media and AI drafts marked 'needs cultural check' stay hidden until approved.",
    ),
    (
        "Mrs Mere Paora",
        "Kaiārahi (cultural guide)",
        "Please do not rank children against each other.",
        "No leaderboard. Reports are kind and never use the word 'Fail'.",
    ),
    (
        "Kiri Rāwiri",
        "Māori community liaison",
        "Use examples our tamariki know, like the marae or the whānau group chat.",
        "New Zealand examples in questions, approved by the Kaiārahi.",
    ),
    (
        "Kiri Rāwiri",
        "Māori community liaison",
        "Ask whānau before you email them.",
        "Parent emails only with consent, and an unsubscribe link in every email.",
    ),
    (
        "Hēmi Te Awa",
        "Māori community liaison",
        "Make it affordable for kura and small rural schools.",
        "A 50% community discount on every plan. Level 1 is always free.",
    ),
    (
        "Hēmi Te Awa",
        "Māori community liaison",
        "Many of our schools have poor internet.",
        "Offline use on one computer, and product keys to switch on a licence without internet.",
    ),
    (
        "Hēmi Te Awa",
        "Māori community liaison",
        "Let the community test it before it goes live.",
        "Community members joined user acceptance testing.",
    ),
]

FRIENDS = [
    ("Mrs Mere Paora", "Kaiārahi (cultural guide)", "Approves Māori content, AI drafts and media."),
    ("Kiri Rāwiri", "Māori community liaison", "Links the team with whānau and kura; Kiwi examples."),
    ("Hēmi Te Awa", "Māori community liaison", "Fair pricing for kura and rural schools; community testing."),
]

TIRITI = [
    ("Partnership (Pātuitanga)", "The Kaiārahi and the liaison roles helped decide what we built, from day one."),
    (
        "Participation (Whai wāhitanga)",
        "Whānau, kura and rural schools took part in meetings and testing. Prices and offline use are fair to them.",
    ),
    (
        "Protection (Tiakitanga)",
        "We protect children's data and Māori cultural knowledge (taonga). AI never profiles children.",
    ),
]
