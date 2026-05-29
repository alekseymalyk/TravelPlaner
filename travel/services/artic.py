import httpx
from django.conf import settings


class ArticAPIError(Exception):
    """Raised when the Art Institute API is unreachable or misbehaves."""


def fetch_artwork(external_id):
    """Fetch a single artwork by its external id.

    Returns the artwork payload (dict) if it exists, or ``None`` if the API
    responds with 404. Raises :class:`ArticAPIError` on network/server errors.
    """
    url = f'{settings.ARTIC_API_BASE_URL}/artworks/{external_id}'
    params = {'fields': 'id,title'}
    try:
        response = httpx.get(url, params=params, timeout=settings.ARTIC_API_TIMEOUT)
    except httpx.HTTPError as exc:
        raise ArticAPIError(str(exc)) from exc

    if response.status_code == 404:
        return None
    if response.status_code >= 400:
        raise ArticAPIError(f'Unexpected status {response.status_code} from Art Institute API')

    return response.json().get('data')
