from unittest import mock

import pytest
from rest_framework.test import APIClient

from travel.models import Place, TravelProject


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def project():
    return TravelProject.objects.create(name='Chicago trip')


def fake_artwork(external_id):
    return {'id': external_id, 'title': f'Artwork {external_id}'}


@pytest.mark.django_db
def test_create_project_with_places(client):
    with mock.patch('travel.serializers.fetch_artwork', side_effect=fake_artwork):
        response = client.post(
            '/api/projects/',
            {'name': 'Trip', 'places': [{'external_id': '1'}, {'external_id': '2'}]},
            format='json',
        )
    assert response.status_code == 201
    body = response.json()
    assert body['status'] == 'planning'
    assert len(body['places']) == 2
    assert body['places'][0]['title'] == 'Artwork 1'


@pytest.mark.django_db
def test_create_project_rejects_more_than_ten_places(client):
    places = [{'external_id': str(i)} for i in range(11)]
    with mock.patch('travel.serializers.fetch_artwork', side_effect=fake_artwork):
        response = client.post(
            '/api/projects/', {'name': 'Big', 'places': places}, format='json'
        )
    assert response.status_code == 400
    assert TravelProject.objects.count() == 0


@pytest.mark.django_db
def test_create_project_rejects_duplicate_places(client):
    places = [{'external_id': '7'}, {'external_id': '7'}]
    with mock.patch('travel.serializers.fetch_artwork', side_effect=fake_artwork):
        response = client.post(
            '/api/projects/', {'name': 'Dup', 'places': places}, format='json'
        )
    assert response.status_code == 400


@pytest.mark.django_db
def test_add_place_validates_against_external_api(client, project):
    with mock.patch('travel.serializers.fetch_artwork', return_value=None):
        response = client.post(
            f'/api/projects/{project.id}/places/',
            {'external_id': '999999'},
            format='json',
        )
    assert response.status_code == 400
    assert project.places.count() == 0


@pytest.mark.django_db
def test_add_duplicate_place_to_project_is_rejected(client, project):
    Place.objects.create(project=project, external_id='5', title='Artwork 5')
    with mock.patch('travel.serializers.fetch_artwork', side_effect=fake_artwork):
        response = client.post(
            f'/api/projects/{project.id}/places/', {'external_id': '5'}, format='json'
        )
    assert response.status_code == 400
    assert project.places.count() == 1


@pytest.mark.django_db
def test_add_place_enforces_limit(client, project):
    for i in range(10):
        Place.objects.create(project=project, external_id=str(i), title=f'Artwork {i}')
    with mock.patch('travel.serializers.fetch_artwork', side_effect=fake_artwork):
        response = client.post(
            f'/api/projects/{project.id}/places/', {'external_id': '99'}, format='json'
        )
    assert response.status_code == 400
    assert project.places.count() == 10


@pytest.mark.django_db
def test_project_completed_when_all_places_visited(client, project):
    place = Place.objects.create(project=project, external_id='1', title='Artwork 1')
    response = client.patch(
        f'/api/projects/{project.id}/places/{place.id}/',
        {'visited': True},
        format='json',
    )
    assert response.status_code == 200
    project.refresh_from_db()
    assert project.status == TravelProject.Status.COMPLETED


@pytest.mark.django_db
def test_project_with_visited_place_cannot_be_deleted(client, project):
    Place.objects.create(project=project, external_id='1', title='Artwork 1', visited=True)
    response = client.delete(f'/api/projects/{project.id}/')
    assert response.status_code == 400
    assert TravelProject.objects.filter(id=project.id).exists()


@pytest.mark.django_db
def test_project_without_visited_places_can_be_deleted(client, project):
    Place.objects.create(project=project, external_id='1', title='Artwork 1')
    response = client.delete(f'/api/projects/{project.id}/')
    assert response.status_code == 204
    assert not TravelProject.objects.filter(id=project.id).exists()
