from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from building.models import Town


class Command(BaseCommand):
    help = 'Adds ressources'

    def handle(self, *args, **kwargs):
        for town in Town.objects.all():
            capacity = town.get_capacity()
            town.add_ressources(capacity, capacity, capacity, capacity)

        self.stdout.write(self.style.SUCCESS(f'Ressources added.'))
