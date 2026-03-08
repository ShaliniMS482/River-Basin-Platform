import pytest
from hydrology.models import RainfallEvent


@pytest.mark.django_db
def test_event_redetection_idempotency(client):

    basin_id = 1

    client.post(f"/api/basins/{basin_id}/detect-events/?min_dry_gap_hours=6")

    first_count = RainfallEvent.objects.count()

    client.post(f"/api/basins/{basin_id}/detect-events/?min_dry_gap_hours=6")

    second_count = RainfallEvent.objects.count()

    assert first_count == second_count
