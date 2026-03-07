from rest_framework import serializers
from .models import Basin, Observation, RainfallEvent, MeasurementType


class BasinSerializer(serializers.ModelSerializer):
    class Meta:
        model = Basin
        fields = "__all__"

class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = "__all__"

class ObservationSerializer(serializers.ModelSerializer):

    basin = serializers.PrimaryKeyRelatedField(
        queryset=Basin.objects.all()
    )

    measurement_type = serializers.PrimaryKeyRelatedField(
        queryset=MeasurementType.objects.all()
    )

    class Meta:
        model = Observation
        fields = "__all__"

class RainfallEventSerializer(serializers.ModelSerializer):

    basin = serializers.PrimaryKeyRelatedField(
        queryset=Basin.objects.all()
    )

    class Meta:
        model = RainfallEvent
        fields = "__all__"
        read_only_fields = ["detected_at"]