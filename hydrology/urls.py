from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BasinViewSet, ObservationViewSet, RainfallEventViewSet, BasinTimeseriesView, \
    DetectRainfallEventsView, BasinEventsView, EventTimeseriesView, BasinEventSummaryView

router = DefaultRouter()

router.register(r'basins', BasinViewSet)
router.register(r'observations', ObservationViewSet)
router.register(r'events', RainfallEventViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("basins/<int:id>/timeseries/", BasinTimeseriesView.as_view()),
    path("basins/<int:id>/detect-events/", DetectRainfallEventsView.as_view()),
    path("basins/<int:id>/events/", BasinEventsView.as_view()),
    path("events/<int:event_id>/timeseries/", EventTimeseriesView.as_view()),
    path("basins/<int:id>/event-summary/", BasinEventSummaryView.as_view()),
]
