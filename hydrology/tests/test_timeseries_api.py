import pytest
from hydrology.models import Basin, MeasurementType, Observation
from django.utils import timezone


@pytest.mark.django_db
def test_timeseries_returns_data(client):

    basin = Basin.objects.create(basin_id=10, name="Basin")

    rainfall = MeasurementType.objects.create(name="rainfall", unit="mm/hr")

    Observation.objects.create(
        basin=basin,
        measurement_type=rainfall,
        timestamp=timezone.datetime(2024, 1, 1, 1, tzinfo=timezone.UTC),
        value=5,
    )

    response = client.get(
        f"/api/basins/{basin.id}/timeseries/?measurement_type=rainfall&from=2024-01-01&to=2024-01-02"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 1
    assert len(data["results"]) == 1


@pytest.mark.django_db
def test_timeseries_no_data(client):

    basin = Basin.objects.create(basin_id=11, name="Empty Basin")
    MeasurementType.objects.create(name="rainfall", unit="mm/hr")

    response = client.get(
        f"/api/basins/{basin.id}/timeseries/?measurement_type=rainfall&from=2024-01-01&to=2024-01-02"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 0
    assert data["results"] == []
