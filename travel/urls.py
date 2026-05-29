from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PlaceViewSet, TravelProjectViewSet

router = DefaultRouter()
router.register('projects', TravelProjectViewSet, basename='project')

place_list = PlaceViewSet.as_view({'get': 'list', 'post': 'create'})
place_detail = PlaceViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})

urlpatterns = router.urls + [
    path('projects/<int:project_pk>/places/', place_list, name='place-list'),
    path('projects/<int:project_pk>/places/<int:pk>/', place_detail, name='place-detail'),
]
