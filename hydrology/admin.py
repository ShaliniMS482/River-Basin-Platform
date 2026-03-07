from django.contrib import admin
from .models import Basin, MeasurementType, Observation, RainfallEvent
# Register your models here.

admin.site.register(Basin)
admin.site.register(MeasurementType)
admin.site.register(Observation)
admin.site.register(RainfallEvent)