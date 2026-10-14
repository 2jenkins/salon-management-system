from django.contrib import admin

from .forms import ServiceForm
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
	form = ServiceForm
	list_display = ('name', 'price', 'duration_minutes')
	search_fields = ('name', 'description')
