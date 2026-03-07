import csv
from django.core.management.base import BaseCommand
from hydrology.models import Basin, MeasurementType, Observation
from dateutil import parser
from django.utils import timezone


class Command(BaseCommand):
    help = "Ingest rainfall and temperature observations"

    def add_arguments(self, parser):
        parser.add_argument('--rainfall', type=str, help='Rainfall CSV file path')
        parser.add_argument('--temperature', type=str, help='Temperature CSV file path')

    def handle(self, *args, **kwargs):

        rainfall_file = kwargs['rainfall']
        temperature_file = kwargs['temperature']

        ingested = 0
        skipped = 0
        errors = 0

        def process_file(file_path, measurement_name):

            nonlocal ingested, skipped, errors

            measurement_type, _ = MeasurementType.objects.get_or_create(
                name=measurement_name,
                defaults={'unit': 'mm' if measurement_name == "Rainfall" else 'C'}
            )

            with open(file_path, 'r') as file:

                reader = csv.DictReader(file)

                for row in reader:

                    try:

                        timestamp_str = row.get('datetime') or row.get('Datetime')
                        value = row.get('value') or row.get('Value')
                        basin_id = row.get('basin') or row.get('Basin.ID')

                        if not timestamp_str or not value or not basin_id:
                            skipped += 1
                            continue

                        timestamp = parser.parse(timestamp_str)
                        if timezone.is_naive(timestamp):
                            timestamp = timezone.make_aware(timestamp)

                        timestamp = timestamp.astimezone(timezone.UTC)

                        value = float(value)
                        basin_id = int(basin_id)

                        basin, _ = Basin.objects.get_or_create(
                            basin_id=basin_id,
                            defaults={"name": f"Basin {basin_id}"}
                        )

                        obj, created = Observation.objects.get_or_create(
                            basin=basin,
                            measurement_type=measurement_type,
                            timestamp=timestamp,
                            defaults={
                                "value": value,
                                "source": "csv_import"
                            }
                        )

                        if created:
                            ingested += 1
                        else:
                            skipped += 1

                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f"Row error: {row} | Error: {e}"))

        if rainfall_file:
            process_file(rainfall_file, "Rainfall")

        if temperature_file:
            process_file(temperature_file, "Temperature")

        self.stdout.write(self.style.SUCCESS(
            f"Ingestion Complete\n"
            f"Rows Ingested: {ingested}\n"
            f"Rows Skipped: {skipped}\n"
            f"Errors: {errors}"
        ))