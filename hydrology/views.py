from rest_framework import viewsets
from .models import Basin, Observation, RainfallEvent
from .serializers import BasinSerializer, ObservationSerializer, RainfallEventSerializer, MeasurementType
from rest_framework.mixins import DestroyModelMixin
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Max
from .pagination import StandardPagination
from django.core.cache import cache
from .helpers import make_cache_key, invalidate_basin_cache
# Create your views here.


class BasinViewSet(viewsets.ModelViewSet):
    queryset = Basin.objects.all().order_by("basin_id")
    serializer_class = BasinSerializer

    filter_backends = [SearchFilter]
    search_fields = ["basin_id", "name"]

class ObservationViewSet(viewsets.ModelViewSet):
    queryset = Observation.objects.select_related(
        "basin",
        "measurement_type"
    ).all().order_by("timestamp")
    serializer_class = ObservationSerializer

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter
    ]

    filterset_fields = {
        "measurement_type": ["exact"],
        "value": ["gte", "lte"],
        "timestamp": ["gte", "lte"],
        "basin": ["exact"]
    }
    ordering_fields = ["timestamp", "value"]

    def perform_create(self, serializer):
        obs = serializer.save()
        invalidate_basin_cache(obs.basin.id)

    def perform_update(self, serializer):
        obs = serializer.save()
        invalidate_basin_cache(obs.basin.id)

    def perform_destroy(self, instance):
        basin_id = instance.basin.id
        instance.delete()
        invalidate_basin_cache(basin_id)

class RainfallEventViewSet(DestroyModelMixin,
                           viewsets.ReadOnlyModelViewSet):

    queryset = RainfallEvent.objects.select_related(
        "basin"
    ).all().order_by("-start_timestamp")
    serializer_class = RainfallEventSerializer

    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter
    ]

    filterset_fields = {
        "basin": ["exact"],
        "min_dry_gap_used": ["exact"],
        "total_volume": ["gte"],
        "start_timestamp": ["gte", "lte"]
    }

    ordering_fields = [
        "start_timestamp",
        "duration_hours",
        "peak_value",
        "total_volume"
    ]

class BasinTimeseriesView(APIView):

    def get(self, request, id):

        measurement = request.query_params.get("measurement_type")
        start = request.query_params.get("from")
        end = request.query_params.get("to")
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", "")

        cache_key = make_cache_key(
            f"basin:{id}:timeseries",
            measurement_type=measurement,
            from_date=start,
            to_date=end,
            page=page,
            page_size=page_size
        )

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        basin = get_object_or_404(Basin, pk=id)
        measurement_obj = MeasurementType.objects.get(name=measurement)

        observations = list(
            Observation.objects
            .select_related("measurement_type")
            .only(
                "timestamp",
                "value",
                "measurement_type__unit"
            )
            .filter(
                basin=basin,
                measurement_type=measurement_obj,
                timestamp__gte=start,
                timestamp__lte=end
            )
            .order_by("timestamp")
        )

        events = list(
            RainfallEvent.objects
            .filter(basin=basin)
            .order_by("start_timestamp")
        )

        results = []

        event_index = 0
        total_events = len(events)

        for obs in observations:

            event_id = None

            while (
                event_index < total_events
                and events[event_index].end_timestamp < obs.timestamp
            ):
                event_index += 1

            if event_index < total_events:

                event = events[event_index]

                if event.start_timestamp <= obs.timestamp <= event.end_timestamp:
                    event_id = event.id

            results.append({
                "timestamp": obs.timestamp,
                "value": obs.value,
                "unit": obs.measurement_type.unit,
                "event_id": event_id
            })

        paginator = StandardPagination()
        page = paginator.paginate_queryset(results, request)
        response = paginator.get_paginated_response(page)

        cache.set(cache_key, response.data, timeout=3600)
        return response
      
class DetectRainfallEventsView(APIView):

    def post(self, request, id):

        basin = get_object_or_404(Basin, pk=id)

        gap = int(request.query_params.get("min_dry_gap_hours", 6))

        rainfall_type = MeasurementType.objects.get(name="rainfall")

        observations = list(
            Observation.objects.filter(
                basin=basin,
                measurement_type=rainfall_type
            ).order_by("timestamp").values("timestamp", "value")
        )

        if not observations:
            return Response({
                "total_events_detected": 0,
                "basin_id": basin.id,
                "min_dry_gap_hours": gap,
                "scan_start": None,
                "scan_end": None
            })

        scan_start = observations[0]["timestamp"]
        scan_end = observations[-1]["timestamp"]

        RainfallEvent.objects.filter(
            basin=basin,
            min_dry_gap_used=gap
        ).delete()

        events = []

        current_start = None
        peak = 0
        volume = 0
        duration = 0
        dry_hours = 0
        last_timestamp = None

        for obs in observations:

            value = obs["value"]
            ts = obs["timestamp"]

            if value > 0:

                if current_start is None:
                    current_start = ts

                peak = max(peak, value)
                volume += value
                duration += 1
                dry_hours = 0
                last_timestamp = ts

            else:

                dry_hours += 1

                if dry_hours >= gap and current_start:

                    events.append(
                        RainfallEvent(
                            basin=basin,
                            start_timestamp=current_start,
                            end_timestamp=last_timestamp,
                            duration_hours=duration,
                            peak_value=peak,
                            total_volume=volume,
                            min_dry_gap_used=gap
                        )
                    )

                    current_start = None
                    peak = 0
                    volume = 0
                    duration = 0
                    dry_hours = 0

        if current_start:
            events.append(
                RainfallEvent(
                    basin=basin,
                    start_timestamp=current_start,
                    end_timestamp=last_timestamp,
                    duration_hours=duration,
                    peak_value=peak,
                    total_volume=volume,
                    min_dry_gap_used=gap
                )
            )

        RainfallEvent.objects.bulk_create(events)
        
        invalidate_basin_cache(basin.id)

        return Response({
            "total_events_detected": len(events),
            "basin_id": basin.id,
            "min_dry_gap_hours": gap,
            "scan_start": scan_start,
            "scan_end": scan_end
        })   

class BasinEventsView(APIView):

    def get(self, request, id):
        gap = request.query_params.get("min_dry_gap_hours")
        volume = request.query_params.get("min_total_volume")
        page = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", "")

        cache_key = make_cache_key(
            f"basin:{id}:events",
            min_dry_gap_hours=gap or "",
            min_total_volume=volume or "",
            page=page,
            page_size=page_size
        )

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        basin = get_object_or_404(Basin, pk=id)
        qs = RainfallEvent.objects.filter(basin=basin)

        if gap:
            qs = qs.filter(min_dry_gap_used=gap)

        if volume:
            qs = qs.filter(total_volume__gte=volume)

        qs = qs.order_by("-start_timestamp")

        data = qs.values(
            "id",
            "start_timestamp",
            "end_timestamp",
            "duration_hours",
            "peak_value",
            "total_volume"
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(data, request)
        response = paginator.get_paginated_response(page)

        cache.set(cache_key, response.data, timeout=3600)
        return response
    
class EventTimeseriesView(APIView):

    def get(self, request, event_id):

        event = get_object_or_404(RainfallEvent, pk=event_id)

        rainfall_type = MeasurementType.objects.get(name="rainfall")

        observations = Observation.objects.filter(
            basin=event.basin,
            measurement_type=rainfall_type,
            timestamp__gte=event.start_timestamp,
            timestamp__lte=event.end_timestamp
        ).order_by("timestamp")

        data = observations.values(
            "timestamp",
            "value"
        )

        return Response(data)

class BasinEventSummaryView(APIView):

    def get(self, request, id):
        gap = request.query_params.get("min_dry_gap_hours")
        
        cache_key = make_cache_key(
            f"basin:{id}:summary",
            min_dry_gap_hours=gap or ""
        )

        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        basin = get_object_or_404(Basin, pk=id)
        events = RainfallEvent.objects.filter(basin=basin)

        if gap is not None:
            events = events.filter(min_dry_gap_used=gap)

        stats = events.aggregate(
            mean_duration=Avg("duration_hours"),
            mean_volume=Avg("total_volume"),
            peak_value=Max("peak_value")
        )

        peak_event = events.order_by("-peak_value").first()
        longest_event = events.order_by("-duration_hours").first()
        total_events = events.count()

        response = {
            "total_events": total_events,
            "mean_duration": stats["mean_duration"],
            "mean_total_volume": stats["mean_volume"],
            "peak_event": peak_event.id if peak_event else None,
            "longest_event": longest_event.id if longest_event else None,
            "min_dry_gap_hours": gap
        }

        cache.set(cache_key, response, timeout=3600)
        return Response(response)
