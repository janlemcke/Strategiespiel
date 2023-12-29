from datetime import datetime, timedelta

# Create your models here.
from django.contrib.auth.models import User
from django.db import models

from building.tasks import set_construction_timer


class Building(models.Model):
    is_production_building = False
    level = models.PositiveIntegerField(default=0)
    under_construction = models.BooleanField(default=False)
    construction_started_at = models.DateTimeField(null=True)
    construction_finished_at = models.DateTimeField(null=True)

    name = ""
    description = ""
    lvl_costs = None
    lvl_time = None

    class Meta:
        abstract = True

    def get_icon(self):
        pass

    def get_name(self) -> str:
        return self.name

    def get_level(self) -> int:
        return self.level

    def get_max_level(self) -> int:
        return len(self.lvl_costs) - 1

    def get_description(self) -> str:
        return self.description

    def can_upgrade(self) -> bool:
        if (self.level + 1 not in self.lvl_costs) or self.under_construction:
            return False

        wood, stone, gold, tools = self.town.get_ressources()

        resources = self.lvl_costs[self.level]

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
            self.construction_finished_at = datetime.utcnow() + timedelta(seconds=self.lvl_time[self.level])
            set_construction_timer.apply_async(args=[self.town.pk], eta=self.construction_finished_at)

            # Add costs to town resources
            costs = self.lvl_costs[self.level]
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
        if self.level + 1 not in self.lvl_costs:
            return {}

        costs = self.lvl_costs[self.level].copy()
        wood, stone, gold, tools = self.town.get_ressources()

        costs["wood"] = max(0, costs["wood"] - wood)
        costs["stone"] = max(0, costs["stone"] - stone)
        costs["gold"] = max(0, costs["gold"] - gold)
        costs["tools"] = max(0, costs["tools"] - tools)

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
    lvl_capacity = {0: 325, 1: 350, 2: 400, 3: 450, 4: 500}
    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }

    def upgrade(self):
        self.town.set_capacity(self.lvl_capacity[self.level])
        super().upgrade()


class Barracks(Building):
    name = "Kaserne"
    description = "In der Kaserne werden deine Soldaten ausgebildet. Je höher die Stufe dieses Gebäudes, desto schneller werden deine Soldaten ausgebildet."

    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }


class Church(Building):
    name = "Kapelle"
    description = "In der Kapelle können deine Bürger beten und sich erholen. Je höher die Stufe dieses Gebäudes, desto schneller regenerieren sich deine Bürger."

    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }


class Farm(Building):
    name = "Felder"
    description = "Auf den Feldern werden die Nahrungsmittel für deine Bürger angebaut. Je höher die Stufe dieses Gebäudes, desto mehr Bürger können ernährt werden."

    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }


class CityWall(Building):
    name = "Stadtmauer"
    description = "Die Stadtmauer schützt deine Stadt vor Angriffen. Je höher die Stufe dieses Gebäudes, desto mehr Schaden können die Mauern aushalten."
    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }


class ProductionBuilding(Building):
    is_production_building = True
    lvl_costs = {
        0: {"wood": 10, "stone": 10, "gold": 10, "tools": 10},
        1: {"wood": 20, "stone": 20, "gold": 20, "tools": 20},
        2: {"wood": 40, "stone": 40, "gold": 40, "tools": 40},
        3: {"wood": 80, "stone": 80, "gold": 80, "tools": 80},
        4: {"wood": 160, "stone": 160, "gold": 160, "tools": 160},
    }
    lvl_time = {
        0: 100,
        1: 200,
        2: 300,
        3: 400,
        4: 500,
    }

    lvl_resources = {
        0: 0,
        1: 10,
        2: 20,
        3: 30,
        4: 40,
    }

    class Meta:
        abstract = True

    def get_resource(self):
        return self.lvl_resources[self.level]

    def get_info_table(self):
        rows = ""
        for level in range(self.level + 1):
            costs = self.lvl_costs[level]
            text = str(self.lvl_resources[level])

            table_row = f"<tr><td>{level}</td><td>{text}</td><td>{costs['wood']}</td><td>{costs['stone']}</td><td>{costs['gold']}</td><td>{costs['tools']}</td></tr>"
            rows += table_row

        return rows

    def get_stats(self):
        costs = self.lvl_costs[self.level]
        has_next_level = self.level + 1 in self.lvl_costs
        text = f"{self.get_resource()} -> {self.lvl_resources[self.level + 1]}" if has_next_level else f"{self.get_resource()}"
        stats = [("Produktion pro Stunde", text),
                 ("Holz", costs["wood"]),
                 ("Stein", costs["stone"]),
                 ("Gold", costs["gold"]),
                 ("Werkzeug", costs["tools"])]
        return stats


class Lumberjack(ProductionBuilding):
    name = "Holzfäller"
    description = "Der Holzfäller bewirtschaftet ein Stück Wald in der Nähe eurer Stadt und produziert Holz. Je höher die Stufe dieses Gebäudes, desto schneller wird Holz produziert."


class StoneMine(ProductionBuilding):
    name = "Steinmine"
    description = "In den Steinminen schuften die Arbeiter, um Stein abzutragen und weiterzuverarbeiten. Je höher die Stufe dieses Gebäudes, desto schneller wird Stein produziert."


class GoldMine(ProductionBuilding):
    name = "Goldmine"
    description = "Das glänzende Gold muss tief aus den Minen geschürft und eingeschmloßen werden. Je höher die Stufe dieses Gebäudes, desto schneller wird Gold produziert."


class Forge(ProductionBuilding):
    name = "Schmiede"
    description = "Die Schmiede bietet Platz aus der perfekten Kombination an Materialien die mächtigsten Waffen seiner Zeit zu fertigen. Je höher die Stufe dieses Gebäudes, desto schneller wird Werkzeuge hergestellt."


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

        town.save()
        return town

    def check_capacity(self) -> None:
        self.wood = min(self.wood, self.capacity)
        self.stone = min(self.stone, self.capacity)
        self.gold = min(self.gold, self.capacity)
        self.tools = min(self.tools, self.capacity)

    def update_ressources(self) -> None:
        self.wood += round(self.lumberjack.get_resource() / 60, 2)
        self.stone += round(self.stoneMine.get_resource() / 60, 2)
        self.gold += round(self.goldMine.get_resource() / 60, 2)
        self.tools += round(self.forge.get_resource() / 60, 2)
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

    def check_construction_status(self):
        for building in self.get_all_buildings():
            building.check_construction_status()
