import math

from ninja import NinjaAPI
from ninja.responses import Response

from building.models import Town

api = NinjaAPI(csrf=True)


@api.get("/town/{pk}/resources")
def getResources(request, pk: int):
    try:
        town = Town.objects.get(pk=pk)
    except Town.DoesNotExist:
        return Response({'error': 'Town does not exist'}, status=404)

    # Get the current resource values for the town
    wood, stone, gold, tools = list(map(lambda x: math.floor(x), town.get_ressources()))
    resources = {
        'wood': wood,
        'stone': stone,
        'gold': gold,
        'tools': tools,
    }

    # Return the resource values as a JSON response
    return Response({'resources': resources})
