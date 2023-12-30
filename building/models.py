import math
from datetime import datetime, timedelta
from random import random
from typing import List

import numpy as np
# Create your models here.
from django.contrib.auth.models import User
from django.db import models

from building.tasks import set_construction_timer, train_units
from core import settings


class Building(models.Model):
    MIN_TIME = 10
    is_production_building = False
    level = models.PositiveIntegerField(default=0)
    under_construction = models.BooleanField(default=False)
    construction_started_at = models.DateTimeField(null=True)
    construction_finished_at = models.DateTimeField(null=True)

    name = ""
    description = ""
    max_level = 21

    class Meta:
        abstract = True

    def get_icon(self):
        pass

    def get_name(self) -> str:
        return self.name

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        pass

    def get_lvl_time(self, lvl) -> int:
        pass

    def get_level(self) -> int:
        return self.level

    def get_max_level(self) -> int:
        return self.max_level

    def get_description(self) -> str:
        return self.description

    def can_upgrade(self) -> bool:
        if (self.level + 1 == self.max_level) or self.under_construction:
            return False

        wood, stone, gold, tools = self.town.get_ressources()

        resources = self.get_lvl_cost(self.level)

        if wood >= resources["wood"] and stone >= resources["stone"] and gold >= resources["gold"] and tools >= \
                resources["tools"]:
            return True
        else:
            return False

    def upgrade(self) -> None:
        if self.can_upgrade():
            # Set construction
            self.under_construction = True
            self.construction_started_at = datetime.utcnow()
            self.construction_finished_at = datetime.utcnow() + timedelta(seconds=self.get_lvl_time(self.level))
            set_construction_timer.apply_async(args=[self.town.pk, self.name], eta=self.construction_finished_at)

            # Add costs to town resources
            costs = self.get_lvl_cost(self.level)
            self.town.add_ressources(wood=-costs["wood"], stone=-costs["stone"], gold=-costs["gold"],
                                     tools=-costs["tools"])
            self.save()

    def get_stats(self):
        pass

    def is_under_construction(self) -> bool:
        return self.under_construction

    def check_construction_status(self) -> None:
        if self.is_under_construction():
            self.construction_started_at = None
            self.construction_finished_at = None
            self.under_construction = False
            self.level += 1
            self.save()

    def get_needed_resources(self) -> dict:
        if self.level + 1 == self.max_level:
            return {}

        costs = self.get_lvl_cost(self.level).copy()
        wood, stone, gold, tools = self.town.get_ressources()

        costs["wood"] = math.ceil(max(0, costs["wood"] - wood))
        costs["stone"] = math.ceil(max(0, costs["stone"] - stone))
        costs["gold"] = math.ceil(max(0, costs["gold"] - gold))
        costs["tools"] = math.ceil(max(0, costs["tools"] - tools))

        if costs["wood"] == 0:
            del costs["wood"]
        if costs["stone"] == 0:
            del costs["stone"]
        if costs["gold"] == 0:
            del costs["gold"]
        if costs["tools"] == 0:
            del costs["tools"]

        return costs


class Storage(Building):
    name = "Lager"
    description = "Im Lager deiner Stadt werden die Resourcen aufbewahrt. Je höher die Stufe dieses gebäudes, desto mehr Resouren kann deine Stadt maximal lagern."

    def get_lvl_capacity(self, lvl) -> int:
        return 300 + 50 * lvl

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": 10 * lvl,
            "stone": 15 * lvl,
            "gold": 5 * lvl,
            "tools": 2 * lvl,
        }
        return costs

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 10 * lvl

    def check_construction_status(self) -> None:
        self.town.set_capacity(self.get_lvl_capacity(self.level))
        super().check_construction_status()

    def upgrade(self):
        super().upgrade()

    def get_info_table(self):
        rows = ""
        for level in range(self.max_level):
            costs = self.get_lvl_cost(level)
            capacity = str(self.get_lvl_capacity(level))
            time_in_seconds = math.ceil(self.get_lvl_time(level))
            time_in_minutes = time_in_seconds // 60
            time_in_hours = time_in_minutes // 60
            time_in_days = time_in_hours // 24

            time_in_days = math.floor(time_in_days)
            time_in_hours = time_in_hours % 24
            time_in_minutes = time_in_minutes % 60
            time_in_seconds = time_in_seconds % 60

            # only show days and hours if there are any
            if time_in_days > 0:
                time = f"{time_in_days}d {time_in_hours}h {time_in_minutes}m {time_in_seconds}s"
            elif time_in_hours > 0:
                time = f"{time_in_hours}h {time_in_minutes}m {time_in_seconds}s"
            elif time_in_minutes > 0:
                time = f"{time_in_minutes}m {time_in_seconds}s"
            else:
                time = f"{time_in_seconds}s"

            costs["wood"] = math.ceil(costs["wood"])
            costs["stone"] = math.ceil(costs["stone"])
            costs["gold"] = math.ceil(costs["gold"])
            costs["tools"] = math.ceil(costs["tools"])

            table_row = f"<tr><td>{level}</td><td>{capacity}</td><td>{time}</td><td>{costs['wood']}</td><td>{costs['stone']}</td><td>{costs['gold']}</td><td>{costs['tools']}</td></tr>"
            rows += table_row

        return rows


class Barracks(Building):
    name = "Kaserne"
    description = "In der Kaserne werden deine Soldaten ausgebildet. Je höher die Stufe dieses Gebäudes, desto schneller werden deine Soldaten ausgebildet."

    javelin_thrower = models.PositiveIntegerField(default=0)
    swordsman = models.PositiveIntegerField(default=0)
    archer = models.PositiveIntegerField(default=0)

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": 4 * lvl,
            "stone": 25 * lvl,
            "gold": 24 * lvl,
            "tools": 14 * lvl,
        }
        return costs

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 10 * lvl

    def get_lvl_speed_multiplier(self, lvl) -> int:
        return 1 + lvl * 0.1

    def add_units(self, unit_amounts: List[int]) -> None:
        self.javelin_thrower += unit_amounts[0]
        self.swordsman += unit_amounts[1]
        self.archer += unit_amounts[2]
        self.save()

    def train_units(self, unit_amounts: List[int]) -> None:
        cost_wood = 0
        cost_stone = 0
        cost_gold = 0
        cost_tools = 0

        train_time_in_secods = 0

        for i, unit in enumerate(settings.GAME_STATS["units"]):
            cost_wood += unit["wood"] * unit_amounts[i]
            cost_stone += unit["stone"] * unit_amounts[i]
            cost_gold += unit["gold"] * unit_amounts[i]
            cost_tools += unit["tools"] * unit_amounts[i]
            train_time_in_secods += unit["train_time"] * unit_amounts[i]

        train_time_in_secods /= self.get_lvl_speed_multiplier(self.level)

        self.town.add_ressources(wood=-cost_wood, stone=-cost_stone, gold=-cost_gold, tools=-cost_tools)
        train_units.apply_async(args=[self.town.pk, unit_amounts], eta=datetime.utcnow() + timedelta(seconds=train_time_in_secods))


class Church(Building):
    name = "Kapelle"
    description = "In der Kapelle können deine Bürger beten und sich erholen. Je höher die Stufe dieses Gebäudes, desto schneller regenerieren sich deine Bürger."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": 30 * lvl,
            "stone": 40 * lvl,
            "gold": 15 * lvl,
            "tools": 10 * lvl,
        }
        return costs

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 50 * lvl


class Farm(Building):
    name = "Felder"
    description = "Auf den Feldern werden die Nahrungsmittel für deine Bürger angebaut. Je höher die Stufe dieses Gebäudes, desto mehr Bürger können ernährt werden."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": 10 * lvl,
            "stone": 5 * lvl,
            "gold": 20 * lvl,
            "tools": 10 * lvl,
        }
        return costs

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 0.5 * lvl ** 2


class CityWall(Building):
    name = "Stadtmauer"
    description = "Die Stadtmauer schützt deine Stadt vor Angriffen. Je höher die Stufe dieses Gebäudes, desto mehr Schaden können die Mauern aushalten."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": 10 * lvl,
            "stone": 5 * lvl ** 1.3,
            "gold": 20 * lvl,
            "tools": 10 * lvl,
        }
        return costs

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 50 * lvl * 3


class ProductionBuilding(Building):
    is_production_building = True
    multiplier = models.FloatField(default=1)

    class Meta:
        abstract = True

    def get_resource(self, level) -> int:
        return math.floor((30 + level ** 1.5) * self.multiplier)

    def get_lvl_time(self, lvl) -> int:
        return self.MIN_TIME + 25 * lvl ** 3

    def get_info_table(self):
        rows = ""
        for level in range(self.max_level):
            costs = self.get_lvl_cost(level)
            text = str(self.get_resource(level))
            time_in_seconds = math.ceil(self.get_lvl_time(level))
            time_in_minutes = time_in_seconds // 60
            time_in_hours = time_in_minutes // 60
            time_in_days = time_in_hours // 24

            time_in_days = math.floor(time_in_days)
            time_in_hours = time_in_hours % 24
            time_in_minutes = time_in_minutes % 60
            time_in_seconds = time_in_seconds % 60

            # only show days and hours if there are any
            if time_in_days > 0:
                time = f"{time_in_days}d {time_in_hours}h {time_in_minutes}m {time_in_seconds}s"
            elif time_in_hours > 0:
                time = f"{time_in_hours}h {time_in_minutes}m {time_in_seconds}s"
            elif time_in_minutes > 0:
                time = f"{time_in_minutes}m {time_in_seconds}s"
            else:
                time = f"{time_in_seconds}s"

            costs["wood"] = math.ceil(costs["wood"])
            costs["stone"] = math.ceil(costs["stone"])
            costs["gold"] = math.ceil(costs["gold"])
            costs["tools"] = math.ceil(costs["tools"])

            table_row = f"<tr><td>{level}</td><td>{text}</td><td>{time}</td><td>{costs['wood']}</td><td>{costs['stone']}</td><td>{costs['gold']}</td><td>{costs['tools']}</td></tr>"
            rows += table_row

        return rows


class Lumberjack(ProductionBuilding):
    name = "Holzfäller"
    description = "Der Holzfäller bewirtschaftet ein Stück Wald in der Nähe eurer Stadt und produziert Holz. Je höher die Stufe dieses Gebäudes, desto schneller wird Holz produziert."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": lvl ** 1.1,
            "stone": lvl ** 1.2,
            "gold": lvl ** 1.3,
            "tools": 5 * lvl,
        }
        return costs


class StoneMine(ProductionBuilding):
    name = "Steinmine"
    description = "In den Steinminen schuften die Arbeiter, um Stein abzutragen und weiterzuverarbeiten. Je höher die Stufe dieses Gebäudes, desto schneller wird Stein produziert."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": lvl ** 1.1,
            "stone": lvl ** 1.2,
            "gold": lvl ** 1.3,
            "tools": 5 * lvl,
        }
        return costs


class GoldMine(ProductionBuilding):
    name = "Goldmine"
    description = "Das glänzende Gold muss tief aus den Minen geschürft und eingeschmloßen werden. Je höher die Stufe dieses Gebäudes, desto schneller wird Gold produziert."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": lvl ** 1.1,
            "stone": lvl ** 1.2,
            "gold": lvl ** 1.3,
            "tools": 5 * lvl,
        }
        return costs


class Forge(ProductionBuilding):
    name = "Schmiede"
    description = "Die Schmiede bietet Platz aus der perfekten Kombination an Materialien die mächtigsten Waffen seiner Zeit zu fertigen. Je höher die Stufe dieses Gebäudes, desto schneller wird Werkzeuge hergestellt."

    def get_lvl_cost(self, lvl) -> dict[str, int]:
        costs = {
            "wood": lvl ** 1.1,
            "stone": lvl ** 1.2,
            "gold": lvl ** 1.3,
            "tools": 5 * lvl,
        }
        return costs


class Town(models.Model):
    # Properties
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=24, default="Meine Stadt")

    # Production Buildings
    lumberjack = models.OneToOneField(Lumberjack, on_delete=models.CASCADE, default=0)
    stoneMine = models.OneToOneField(StoneMine, on_delete=models.CASCADE, default=0)
    goldMine = models.OneToOneField(GoldMine, on_delete=models.CASCADE, default=0)
    forge = models.OneToOneField(Forge, on_delete=models.CASCADE, default=0)

    # Buildings
    storage = models.OneToOneField(Storage, on_delete=models.CASCADE, default=0)
    church = models.OneToOneField(Church, on_delete=models.CASCADE, default=0)
    barracks = models.OneToOneField(Barracks, on_delete=models.CASCADE, default=0)
    cityWall = models.OneToOneField(CityWall, on_delete=models.CASCADE, default=0)
    farm = models.OneToOneField(Farm, on_delete=models.CASCADE, default=0)

    # Ressourcen
    wood = models.FloatField(default=0)
    stone = models.FloatField(default=0)
    gold = models.FloatField(default=0)
    tools = models.FloatField(default=0)
    capacity = models.IntegerField(default=300)

    @classmethod
    def create(cls, user):
        town = cls(user=user)

        # Production Buildings
        town.lumberjack = Lumberjack.objects.create()
        town.stoneMine = StoneMine.objects.create()
        town.goldMine = GoldMine.objects.create()
        town.forge = Forge.objects.create()

        # Buildings
        town.storage = Storage.objects.create()
        town.church = Church.objects.create()
        town.barracks = Barracks.objects.create()
        town.cityWall = CityWall.objects.create()
        town.farm = Farm.objects.create()

        town.name = user.username + "s Stadt"

        # Starter ressources
        town.wood = 300
        town.stone = 300
        town.gold = 300
        town.tools = 300
        town.capacity = 300

        multiplier = [0.5 + random() * 0.5, 0.75 + random() * 0.25, 1 + random() * 0.5, 1 + random() * 0.5]
        np.random.shuffle(multiplier)

        town.lumberjack.multiplier = multiplier[0]
        town.stoneMine.multiplier = multiplier[1]
        town.goldMine.multiplier = multiplier[2]
        town.forge.multiplier = multiplier[3]

        town.lumberjack.save()
        town.stoneMine.save()
        town.goldMine.save()
        town.forge.save()

        town.save()
        return town

    def check_capacity(self) -> None:
        self.wood = min(self.wood, self.capacity)
        self.stone = min(self.stone, self.capacity)
        self.gold = min(self.gold, self.capacity)
        self.tools = min(self.tools, self.capacity)

    def update_ressources(self) -> None:
        self.wood += round(self.lumberjack.get_resource(self.lumberjack.level) / 60, 2)
        self.stone += round(self.stoneMine.get_resource(self.stoneMine.level) / 60, 2)
        self.gold += round(self.goldMine.get_resource(self.goldMine.level) / 60, 2)
        self.tools += round(self.forge.get_resource(self.forge.level) / 60, 2)
        self.check_capacity()
        self.save()

    def add_ressources(self, wood, stone, gold, tools) -> None:
        self.wood += wood
        self.stone += stone
        self.gold += gold
        self.tools += tools
        self.check_capacity()
        self.save()

    def set_capacity(self, amount) -> None:
        self.capacity = amount
        self.save()

    def get_production_buildings(self) -> [ProductionBuilding]:
        return [self.lumberjack, self.stoneMine, self.goldMine, self.forge]

    def get_buildings(self) -> [Building]:
        return [self.storage, self.barracks, self.cityWall, self.church, self.farm]

    def get_ressources(self) -> [float]:
        return [self.wood, self.stone, self.gold, self.tools]

    def get_all_buildings(self) -> [Building]:
        return self.get_buildings() + self.get_production_buildings()

    def get_capacity(self) -> int:
        return self.capacity

    def check_construction_status(self, building_name):
        for building in self.get_all_buildings():
            if building.get_name() == building_name:
                building.check_construction_status()
