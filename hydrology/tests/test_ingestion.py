import pytest
from django.core.management import call_command
from hydrology.models import Observation


@pytest.mark.django_db
def test_ingestion_idempotency():

    call_command(
        "ingest_observations",
        rainfall="sample_data/january_rain.csv",
        temperature="sample_data/january_temp.csv",
    )

    first_count = Observation.objects.count()

    call_command(
        "ingest_observations",
        rainfall="sample_data/january_rain.csv",
        temperature="sample_data/january_temp.csv",
    )

    second_count = Observation.objects.count()

    assert first_count == second_count
