import math
from typing import List, Tuple

from core import settings
from ninja import Router, Schema
from ninja.responses import Response

from building.models import Town

router = Router()


class ResourceOut(Schema):
    resources: List[Tuple[int, str]]
    capacity: int


class BuildingsOut(Schema):
    name: str
    level: int
    under_construction: bool
    construction_started_at: str
    construction_finished_at: str
    can_upgrade: bool
    needed_resources: dict[str, int]


class BuildingUpgradabilityOut(Schema):
    name: str
    can_upgrade: bool
    needed_resources: dict[str, int]


class UnitCostsOut(Schema):
    costs: List[List[int]]


class TrainUnits(Schema):
    unit_amounts: List[int]


@router.get("/{pk}/resources", response=ResourceOut, description="Get all current resources of a town")
def get_resources(request, pk: int):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    # Get the current resource values for the town
    resource_list = town.get_ressources()
    capacity = town.get_capacity()
    dates = []
    for i, prod in enumerate(town.get_production_buildings()):
        production_rate_per_hour = prod.get_resource(prod.level)
        resource = resource_list[i]
        time_left = (capacity - resource) / production_rate_per_hour
        time_left_hours = math.floor(time_left)
        time_left_minutes = math.floor((time_left - time_left_hours) * 60)
        dates.append(f"{time_left_hours}h {time_left_minutes}m")

    resources = list(zip(map(lambda x: math.floor(x), resource_list), dates))
    resources = ResourceOut(resources=resources, capacity=capacity)

    return Response(resources)


@router.get("/{pk}/buildings", response=List[BuildingsOut],
            description="Get all all buildings of a town")
def get_buildings(request, pk: int):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    buildings = []
    for building in town.get_all_buildings():
        construction_finished_at = str(building.construction_finished_at) if building.is_under_construction() else ""
        construction_started_at = str(building.construction_started_at) if building.is_under_construction() else ""
        needed_resources = building.get_needed_resources()
        serialized_building = BuildingsOut(name=building.get_name(),
                                           level=building.get_level(),
                                           under_construction=building.is_under_construction(),
                                           construction_started_at=construction_started_at,
                                           construction_finished_at=construction_finished_at,
                                           can_upgrade=building.can_upgrade(),
                                           needed_resources=needed_resources)
        buildings.append(serialized_building)

    return Response(buildings)


@router.get("/{pk}/buildings/upgradable", response=List[BuildingUpgradabilityOut],
            description="Get a list of buildings and if they are upgradable of a town")
def get_buildings_upgradability(request, pk: int):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    buildings = []
    for building in town.get_all_buildings():
        needed_resources = building.get_needed_resources()
        serialized_building = BuildingUpgradabilityOut(name=building.get_name(),
                                                       can_upgrade=building.can_upgrade(),
                                                       needed_resources=needed_resources)
        buildings.append(serialized_building)

    return Response(buildings)


@router.get("/{pk}/buildings/{building_name}", response=BuildingsOut,
            description="Get one building of a town")
def get_building(request, pk: int, building_name: str):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    for building in town.get_all_buildings():
        if building.get_name() == building_name:
            construction_finished_at = str(
                building.construction_finished_at) if building.is_under_construction() else ""
            construction_started_at = str(building.constuction_started_at) if building.is_under_construction() else ""
            serialized_building = BuildingsOut(name=building.get_name(),
                                               level=building.get_level(),
                                               under_construction=building.is_under_construction(),
                                               construction_started_at=construction_started_at,
                                               construction_finished_at=construction_finished_at,
                                               can_upgrade=building.can_upgrade())
            return Response(serialized_building)

    return Response({'error': 'Building does not exist'}, status=404)


@router.get("/unit/costs", response=UnitCostsOut,
            description="Get unit costs of a town")
def get_unit_cost(request):
    stats = settings.GAME_STATS
    response_list = []
    for unit in stats["units"]:
        response_list.append([unit["wood"], unit["stone"], unit["gold"], unit["tools"]])

    return Response(UnitCostsOut(costs=response_list), status=200)


@router.post("/{pk}/buildings/{building_name}/upgrade", description="Upgrade a building")
def upgrade_building(request, pk: int, building_name: str):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    for building in town.get_all_buildings():
        if building.get_name() == building_name:
            building.upgrade()
            return Response({'success': 'Building upgrade started'}, status=200)

    return Response({'error': 'Building does not exist'}, status=404)


@router.post("/{pk}/barracks/train", description="Train units")
def upgrade_building(request, pk: int, trainUnits: TrainUnits):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    town.barracks.train_units(trainUnits.unit_amounts)

    return Response({'success': 'Units training started'}, status=200)
