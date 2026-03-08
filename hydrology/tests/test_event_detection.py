import pytest
from datetime import timedelta
from hydrology.models import Basin, MeasurementType, Observation
from django.utils import timezone


@pytest.mark.django_db
def test_single_rainfall_event(client):

    basin = Basin.objects.create(basin_id=1, name="Test Basin")

    rainfall = MeasurementType.objects.create(name="rainfall", unit="mm/hr")

    base = timezone.datetime(2024,1,1, tzinfo=timezone.UTC)

    values = [0, 0, 2, 3, 1, 0, 0]

    for i, v in enumerate(values):
        Observation.objects.create(
            basin=basin,
            measurement_type=rainfall,
            timestamp=base + timedelta(hours=i),
            value=v,
        )

    response = client.post(f"/api/basins/{basin.id}/detect-events/?min_dry_gap_hours=3")

    assert response.status_code == 200
    assert response.data["total_events_detected"] == 1


@pytest.mark.django_db
def test_two_events_when_gap_exceeds_threshold(client):

    basin = Basin.objects.create(basin_id=2, name="Test Basin")

    rainfall = MeasurementType.objects.create(name="rainfall", unit="mm/hr")

    base = timezone.datetime(2024,1,1, tzinfo=timezone.UTC)

    values = [0, 2, 3, 0, 0, 0, 0, 4, 5, 0]

    for i, v in enumerate(values):
        Observation.objects.create(
            basin=basin,
            measurement_type=rainfall,
            timestamp=base + timedelta(hours=i),
            value=v,
        )

    response = client.post(f"/api/basins/{basin.id}/detect-events/?min_dry_gap_hours=3")

    assert response.data["total_events_detected"] == 2


@pytest.mark.django_db
def test_gap_smaller_than_threshold_merges_events(client):

    basin = Basin.objects.create(basin_id=3, name="Test Basin")

    rainfall = MeasurementType.objects.create(name="rainfall", unit="mm/hr")

    base = timezone.datetime(2024,1,1, tzinfo=timezone.UTC)

    values = [0, 2, 3, 0, 1, 2, 0]

    for i, v in enumerate(values):
        Observation.objects.create(
            basin=basin,
            measurement_type=rainfall,
            timestamp=base + timedelta(hours=i),
            value=v,
        )

    response = client.post(f"/api/basins/{basin.id}/detect-events/?min_dry_gap_hours=5")

    assert response.data["total_events_detected"] == 1
