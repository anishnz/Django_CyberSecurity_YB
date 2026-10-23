"""
models.py - Public website content: slider, team photos, meeting photos, contact messages
==========================================================================================

Owner: Dinesh Upreti (public website)

Concepts:
    * Inheritance with an abstract model: ``PublicImage`` holds the fields every
      public picture needs (order, on/off). ``TeamMember`` and ``MeetingPhoto``
      inherit them, so Django makes two tables but we write the shared code once.
    * Encapsulation: ``image_url`` hides "is there a file?" from the templates.
"""

from __future__ import annotations

from django.db import models


class Slide(models.Model):
    """One picture in the home page slider. Super Admin can upload AI-made images later."""

    title = models.CharField(max_length=100)
    caption = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to="website/slides/",
        blank=True,
        help_text="Optional upload (max 5 MB). Without it, the built-in illustration is used.",
    )
    static_image = models.CharField(max_length=120, blank=True, help_text="Built-in illustration in static/img/slides/")
    order = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class PublicImage(models.Model):
    """Abstract parent for pictures shown on the public website."""

    order = models.PositiveSmallIntegerField(default=1, help_text="Smaller numbers are shown first.")
    is_active = models.BooleanField(default=True, help_text="Untick to hide it without deleting it.")

    class Meta:
        abstract = True
        ordering = ["order", "id"]

    def picture(self):
        """The image field of the child class (each child names its field)."""
        raise NotImplementedError

    @property
    def image_url(self) -> str:
        """URL of the uploaded picture, or '' when nothing is uploaded yet."""
        pic = self.picture()
        return pic.url if pic else ""


class TeamMember(PublicImage):
    """One person in our team. The Super Admin uploads the photo on the Website content page."""

    name = models.CharField(max_length=80)
    student_id = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=120)
    bio = models.TextField(max_length=600, blank=True, help_text="Two or three short sentences, in your own words.")
    photo = models.ImageField(upload_to="website/team/", blank=True)

    class Meta(PublicImage.Meta):
        verbose_name = "team member"

    def __str__(self) -> str:
        return self.name

    def picture(self):
        return self.photo

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in self.name.split()[:2]).upper()


class MeetingPhoto(PublicImage):
    """A real photo of one of our team meetings (for the meetings slider)."""

    title = models.CharField(max_length=100)
    caption = models.CharField(max_length=200, blank=True)
    place = models.CharField(max_length=100, default="Auckland")
    taken_on = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to="website/meetings/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta(PublicImage.Meta):
        verbose_name = "meeting photo"

    def __str__(self) -> str:
        return self.title

    def picture(self):
        return self.image


class ContactMessage(models.Model):
    """A message from the Contact us form. It also becomes a help desk ticket."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    organisation = models.CharField(max_length=120, blank=True)
    topic = models.CharField(max_length=40, default="general")
    message = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    ticket_number = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name}: {self.topic}"
