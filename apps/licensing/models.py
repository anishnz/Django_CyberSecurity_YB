"""
models.py - Licence and Level Pack records
==========================================

Owner: Rajneesh Kumar (task R-05)

The database row stores plan code and dates; ``License.plan_obj`` turns it into
the right Plan class (plans.py) so the rules live in Python classes.
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .plans import FREE_LEVEL, PLAN_CHOICES, plan_for


class License(models.Model):
    """A school's current subscription (one per school)."""

    school = models.OneToOneField("schools.School", on_delete=models.CASCADE, related_name="license")
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="TRIAL")
    start_date = models.DateField()
    expiry_date = models.DateField()
    community_discount = models.BooleanField(default=False, help_text="50% discount for kura and small rural schools.")
    product_key = models.CharField(max_length=60, blank=True)
    last_warning_sent = models.DateField(
        null=True, blank=True, help_text="Stops the expiry warning being sent more than once a day."
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.school.code}: {self.get_plan_display()} until {self.expiry_date}"

    @property
    def plan_obj(self):
        """The Plan object with the rules for this plan (polymorphism)."""
        return plan_for(self.plan, self.start_date, self.expiry_date, self.community_discount)


class LevelPack(models.Model):
    """A Level Pack (levels 2–6) bought by a school. Level 1 is always free."""

    school = models.ForeignKey("schools.School", on_delete=models.CASCADE, related_name="level_packs")
    level = models.PositiveSmallIntegerField(validators=[MinValueValidator(FREE_LEVEL + 1), MaxValueValidator(6)])
    product_key = models.CharField(max_length=60, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["level"]
        constraints = [models.UniqueConstraint(fields=["school", "level"], name="one_pack_per_level_per_school")]

    def __str__(self) -> str:
        return f"{self.school.code} Level Pack {self.level}"
