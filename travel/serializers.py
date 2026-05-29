from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from .models import Place, TravelProject
from .services.artic import ArticAPIError, fetch_artwork


def resolve_artwork_title(external_id):
    """Validate that an artwork exists in the Art Institute API and return its title."""
    try:
        artwork = fetch_artwork(external_id)
    except ArticAPIError as exc:
        raise serializers.ValidationError(
            f'Could not reach the Art Institute API: {exc}'
        )
    if artwork is None:
        raise serializers.ValidationError(
            f"Place '{external_id}' was not found in the Art Institute API."
        )
    return artwork.get('title', '')


class PlaceSerializer(serializers.ModelSerializer):
    """Read/update representation of a place within a project."""

    class Meta:
        model = Place
        fields = ['id', 'external_id', 'title', 'notes', 'visited', 'created_at', 'updated_at']
        read_only_fields = ['id', 'title', 'created_at', 'updated_at']

    def validate_external_id(self, value):
        if self.instance is not None:
            return value
        project = self.context.get('project')
        if project and project.places.filter(external_id=value).exists():
            raise serializers.ValidationError(
                'This place has already been added to the project.'
            )
        return value

    def validate(self, attrs):
        # On create, enforce the per-project limit and validate against the API.
        if self.instance is None:
            project = self.context['project']
            if project.places.count() >= settings.MAX_PLACES_PER_PROJECT:
                raise serializers.ValidationError(
                    f'A project cannot have more than {settings.MAX_PLACES_PER_PROJECT} places.'
                )
            attrs['title'] = resolve_artwork_title(attrs['external_id'])
        return attrs


class PlaceInputSerializer(serializers.Serializer):
    """Nested place payload accepted when creating a project."""

    external_id = serializers.CharField(max_length=64)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


class TravelProjectSerializer(serializers.ModelSerializer):
    """Read representation of a project, including its places."""

    places = PlaceSerializer(many=True, read_only=True)

    class Meta:
        model = TravelProject
        fields = [
            'id', 'name', 'description', 'start_date', 'status',
            'places', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class TravelProjectCreateSerializer(serializers.ModelSerializer):
    """Write serializer that allows creating a project together with its places."""

    places = PlaceInputSerializer(many=True, required=False, default=list)

    class Meta:
        model = TravelProject
        fields = ['id', 'name', 'description', 'start_date', 'places']
        read_only_fields = ['id']

    def validate_places(self, value):
        if len(value) > settings.MAX_PLACES_PER_PROJECT:
            raise serializers.ValidationError(
                f'A project cannot have more than {settings.MAX_PLACES_PER_PROJECT} places.'
            )
        external_ids = [place['external_id'] for place in value]
        if len(external_ids) != len(set(external_ids)):
            raise serializers.ValidationError('Duplicate places are not allowed.')
        return value

    def create(self, validated_data):
        places_data = validated_data.pop('places', [])
        resolved = [
            {**place, 'title': resolve_artwork_title(place['external_id'])}
            for place in places_data
        ]
        with transaction.atomic():
            project = TravelProject.objects.create(**validated_data)
            Place.objects.bulk_create(
                Place(project=project, **place) for place in resolved
            )
        return project

    def to_representation(self, instance):
        return TravelProjectSerializer(instance, context=self.context).data
