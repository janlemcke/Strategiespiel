from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from building.models import Town


class Command(BaseCommand):
    help = 'Adds ressources'

    def handle(self, *args, **kwargs):
        Town.objects.first().add_ressources(100, 100, 100, 100)
        self.stdout.write(self.style.SUCCESS(f'Ressources added.'))
