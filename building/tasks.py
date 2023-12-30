from typing import List

from celery import shared_task

from building import models


@shared_task()
def update_resources():
    for town in models.Town.objects.all():
        town.update_ressources()


@shared_task()
def set_construction_timer(town_pk: int, building_name: str):
    town = models.Town.objects.filter(pk=town_pk).first()
    town.check_construction_status(building_name)
    print(f"Construction timer for {building_name} in town {town_pk} completed.")


@shared_task()
def train_units(town_pk: int, unit_amounts: List[int]):
    town = models.Town.objects.filter(pk=town_pk).first()
    town.barracks.add_units(unit_amounts)
    print(f"Training of units {unit_amounts} in town {town_pk} completed.")
