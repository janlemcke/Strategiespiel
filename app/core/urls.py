from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from ninja import NinjaAPI

from account.views import SignUpView
from building.api import router as building_router
from building.views import index
from core import settings

api = NinjaAPI(csrf=True, version="1.0.0")

api.add_router("/town/", building_router, tags=["Town"])

urlpatterns = [
    path("", index, name="home"),
    path('admin/', admin.site.urls),
    path('account/logout/', LogoutView.as_view(next_page="login"), name='logout'),
    path('account/signup', SignUpView.as_view(), name="signup"),
    path('account/', include('django.contrib.auth.urls')),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
