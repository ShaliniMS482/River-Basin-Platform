from django.db import models

# Create your models here.
class Basin(models.Model):
    basin_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Basin {self.basin_id}"
    

class MeasurementType(models.Model):
    name = models.CharField(max_length=50)
    unit = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Observation(models.Model):
    basin = models.ForeignKey(Basin, on_delete=models.CASCADE, related_name="observations")
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    value = models.FloatField()
    source = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['basin', 'measurement_type', 'timestamp'],
                name='unique_observation'
            )
        ]
        indexes = [
            models.Index(fields=['basin', 'timestamp', 'measurement_type'])
        ]

    def __str__(self):
        return f"{self.basin} - {self.measurement_type} - {self.timestamp}"
    

class RainfallEvent(models.Model):
    basin = models.ForeignKey(Basin, on_delete=models.CASCADE, related_name="events")
    start_timestamp = models.DateTimeField()
    end_timestamp = models.DateTimeField()
    duration_hours = models.IntegerField()
    peak_value = models.FloatField()
    total_volume = models.FloatField()
    min_dry_gap_used = models.IntegerField()
    detected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['basin', 'start_timestamp', 'min_dry_gap_used'],
                name='unique_event_per_gap'
            )
        ]

    def __str__(self):
        return f"Event {self.start_timestamp} - {self.end_timestamp}"
    