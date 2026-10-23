"""defaults.py - The starting email templates (Super Admin can edit them later). Owner: Rajneesh Kumar."""

SIGN = "\n\nNgā mihi,\nThe CyberQuest team"

DEFAULT_TEMPLATES = {
    "ticket_opened": ("Ticket opened", "system", "We got your message – ticket {ticket}",
                      "Kia ora {name},\n\nThank you for contacting CyberQuest. Your ticket number is {ticket} "
                      "({title}).\nWe will reply as soon as we can. Please keep this number." + SIGN),
    "ticket_reply": ("Ticket reply", "system", "New reply on ticket {ticket}",
                     "Kia ora {name},\n\nThere is a new reply on your ticket {ticket} ({title}):\n\n{reply}" + SIGN),
    "password_reset": ("Password reset", "system", "Reset your CyberQuest password",
                       "Kia ora {name},\n\nUse this link to choose a new password. It works for 1 hour:\n{link}\n\n"
                       "If you did not ask for this, you can ignore this email." + SIGN),
    "licence_expiring": ("Licence ending soon", "admins", "Your CyberQuest licence ends on {date}",
                         "Kia ora {name},\n\nThe CyberQuest licence for {school} ends on {date}. "
                         "Please renew it so students can keep learning." + SIGN),
    "payment_reviewed": ("Payment reviewed", "admins", "Payment {status}: {reference}",
                         "Kia ora {name},\n\nYour payment {reference} was {status}.\n{note}" + SIGN),
    "parent_progress": ("Progress update for whānau", "parents", "{student}'s CyberQuest progress",
                        "Kia ora {name},\n\n{student} has been learning how to stay safe online at {school}.\n"
                        "This term they finished {levels} level(s). Ask them to show you one thing they learned!"
                        "\n\nTo stop these emails: {unsubscribe}" + SIGN),
    "parent_notice": ("Notice to whānau", "parents", "A message from {school}",
                      "Kia ora {name},\n\n{message}\n\nTo stop these emails: {unsubscribe}" + SIGN),
    "teacher_notice": ("Notice to teachers", "teachers", "CyberQuest update for {school}",
                       "Kia ora {name},\n\n{message}\n\nTo stop these emails: {unsubscribe}" + SIGN),
}
