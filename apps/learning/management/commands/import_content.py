"""import_content - load the 6 levels, 24 topics and 126 questions. Owner: Jihe Qi (task J-13)."""

from django.core.management.base import BaseCommand

from apps.learning.importer import ContentImporter


class Command(BaseCommand):
    help = "Import study topics and question banks from data/ (safe to run again)."

    def handle(self, *args, **options):
        result = ContentImporter().import_all()
        self.stdout.write(self.style.SUCCESS(f"Imported: {result}"))
