from django.urls import path
from preview.views import preview_import

urlpatterns = [
    path('', preview_import, name='preview_import'),
]