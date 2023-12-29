from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from building.models import Town


class Command(BaseCommand):
    help = 'Adds ressources'

    def handle(self, *args, **kwargs):
        town = Town.objects.first()
        capacity = town.get_capacity()
        Town.objects.first().add_ressources(capacity,capacity,capacity,capacity)
        self.stdout.write(self.style.SUCCESS(f'Ressources added.'))
