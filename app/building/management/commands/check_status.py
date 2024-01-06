from django.core.management.base import BaseCommand

from building.models import Town


class Command(BaseCommand):
    help = 'Triggers updating constructions'

    def handle(self, *args, **kwargs):
        for town in Town.objects.all():
            town.check_construction_status()
        self.stdout.write(self.style.SUCCESS(f'Constructions updated.'))