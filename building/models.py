from datetime import datetime, timedelta

# Create your models here.
from django.contrib.auth.models import User
from django.db import models

from building.tasks import set_construction_timer


class Building(models.Model):
    level = models.PositiveIntegerField(default=0)
    under_construction = models.BooleanField(default=False)
    construction_finished_at = models.DateTimeField(null=True)

    name = ""
    description = ""
    lvl_costs = None
    lvl_time = None

    class Meta:
        abstract = True

    def get_icon(self):
        pass

    def get_name(self):
        return self.name

    def get_level(self):
        return self.level

    def get_description(self):
        return self.description

    def can_upgrade(self):
        if (self.level + 1 not in self.lvl_costs) or self.under_construction:
            return False

        wood, stone, gold, tools = self.town.get_ressources()

        resources = self.lvl_costs[self.level]

        if wood >= resources["wood"] and stone >= resources["stone"] and gold >= resources["gold"] and tools >= \
                resources["tools"]:
            return True
        else:
            return False

    def upgrade(self):
        if self.can_upgrade():
            # Set construction
            self.under_construction = True
            self.construction_finished_at = datetime.now() + timedelta(seconds=self.lvl_time[self.level])
            set_construction_timer.apply_async(args=[self.town.pk], countdown=self.lvl_time[self.level])

            # Add costs to town resources
            costs = self.lvl_costs[self.level]
            self.town.add_ressources(wood=-costs["wood"], stone=-costs["stone"], gold=-costs["gold"],
                                     tools=-costs["tools"])
            self.save()

    def get_stats(self):
        pass

    def is_under_construction(self):
        return self.under_construction

    def check_construction_status(self):
        if self.is_under_construction():
            self.construction_finished_at = None
            self.under_construction = False
            self.level += 1
            self.save()


class Storage(Building):
    name = "Lager"
    description = "Im Lager deiner Stadt werden die Resourcen aufbewahrt. Je höher die Stufe dieses gebäudes, desto mehr Resouren kann deine Stadt maximal lagern."
    lvl_capacity = {0: 325, 1: 350, 2: 400}
    lvl_costs = {
        0: {"wood": 10, "stone": 15, "gold": 5, "tools": 2},
        1: {"wood": 15, "stone": 20, "gold": 10, "tools": 4},
        2: {"wood": 150, "stone": 200, "gold": 50, "tools": 47},
    }
    lvl_time = {
        0: 20,
        1: 40,
        2: 1800,
    }

    def upgrade(self):
        self.town.set_capacity(self.lvl_capacity[self.level])
        super().upgrade()


class ProductionBuilding(Building):
    lvl_ressource = {
        0: 0,
        1: 10,
        2: 20,
        3: 30,
    }

    lvl_costs = {
        0: {"wood": 10, "stone": 15, "gold": 5, "tools": 2},
        1: {"wood": 15, "stone": 20, "gold": 10, "tools": 4},
        2: {"wood": 20, "stone": 25, "gold": 15, "tools": 8},
    }

    lvl_time = {
        0: 20,
        1: 40,
        2: 1200,
    }

    class Meta:
        abstract = True

    def get_ressource(self):
        return self.lvl_ressource[self.level]

    def get_stats(self):
        costs = self.lvl_costs[self.level]
        stats = [("Produktion pro Stunde", f"{self.get_ressource()} -> {self.lvl_ressource[self.level + 1]}"),
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

    # Ressourcen
    wood = models.FloatField(default=0)
    stone = models.FloatField(default=0)
    gold = models.FloatField(default=0)
    tools = models.FloatField(default=0)
    capacity = models.IntegerField(default=300)

    @classmethod
    def create(cls, user):
        lumberjack = Lumberjack.objects.create()
        stoneMine = StoneMine.objects.create()
        goldMine = GoldMine.objects.create()
        forge = Forge.objects.create()
        storage = Storage.objects.create()
        town = cls(user=user)
        town.lumberjack = lumberjack
        town.stoneMine = stoneMine
        town.goldMine = goldMine
        town.forge = forge
        town.storage = storage

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
        self.wood += self.lumberjack.get_ressource() / 60
        self.stone += self.stoneMine.get_ressource() / 60
        self.gold += self.goldMine.get_ressource() / 60
        self.tools += self.forge.get_ressource() / 60
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
        return [self.storage]

    def get_ressources(self) -> [float]:
        return [self.wood, self.stone, self.gold, self.tools]

    def get_all_buildings(self) -> [Building]:
        return self.get_buildings() + self.get_production_buildings()

    def get_capacity(self) -> int:
        return self.capacity

    def check_construction_status(self):
        for building in self.get_all_buildings():
            building.check_construction_status()
