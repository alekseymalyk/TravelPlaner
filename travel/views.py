from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Place, TravelProject
from .serializers import (
    PlaceSerializer,
    TravelProjectCreateSerializer,
    TravelProjectSerializer,
)


class TravelProjectViewSet(viewsets.ModelViewSet):
    queryset = TravelProject.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return TravelProjectCreateSerializer
        return TravelProjectSerializer

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.has_visited_places():
            raise ValidationError(
                'A project cannot be deleted while some of its places are marked as visited.'
            )
        return super().destroy(request, *args, **kwargs)


class PlaceViewSet(viewsets.ModelViewSet):
    serializer_class = PlaceSerializer
    http_method_names = ['get', 'post', 'patch']

    def get_project(self):
        return get_object_or_404(TravelProject, pk=self.kwargs['project_pk'])

    def get_queryset(self):
        return Place.objects.filter(project_id=self.kwargs['project_pk'])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context

    def perform_create(self, serializer):
        serializer.save(project=self.get_project())

    def perform_update(self, serializer):
        place = serializer.save()
        place.project.recalculate_status()
