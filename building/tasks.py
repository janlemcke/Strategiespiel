from celery import shared_task

from building import models

@shared_task()
def update_resources():
    for town in models.Town.objects.all():
        town.update_ressources()


@shared_task()
def set_construction_timer(town_pk):
    print("Check construction status for town:", town_pk)
    town = models.Town.objects.filter(pk=town_pk).first()
    town.check_construction_status()
    print("Upgrading completed.")
