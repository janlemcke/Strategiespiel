from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
from building import models as building_models


def upgrade_building(building_name, town):
    for building in town.get_all_buildings():
        if building.get_name() == building_name:
            building.upgrade()


@login_required
def index(request):
    context = {}
    context["town"] = building_models.Town.objects.filter(user=request.user).first()

    if request.POST:
        if "action" in request.POST and "upgrade" in request.POST["action"]:
            upgrade_building(request.POST["action"].split("_")[1], context["town"])
    return render(request, "building/home.html", context)