from django.contrib import admin
from django.contrib import messages
from django.db import IntegrityError, transaction

from .availability import ACTIVE_STATUSES, reserve_appointment_slots
from .models import Appointment, SalonClosure, WeeklySchedule


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
	list_display = ('customer', 'service', 'appointment_date', 'appointment_time', 'status')
	list_filter = ('status', 'appointment_date', 'service')
	search_fields = ('customer__username', 'customer__email', 'service__name')
	readonly_fields = ('customer', 'service', 'appointment_date', 'appointment_time', 'duration_minutes')

	def save_model(self, request, obj, form, change):
		old_status = form.initial.get('status') if change else None
		try:
			with transaction.atomic():
				super().save_model(request, obj, form, change)
				if obj.status in ACTIVE_STATUSES and old_status not in ACTIVE_STATUSES:
					reserve_appointment_slots(obj)
				elif obj.status not in ACTIVE_STATUSES:
					obj.reserved_slots.all().delete()
		except IntegrityError:
			messages.error(request, 'This appointment conflicts with another active booking; its status was not changed.')


@admin.register(WeeklySchedule)
class WeeklyScheduleAdmin(admin.ModelAdmin):
	list_display = ('weekday', 'is_closed', 'opens_at', 'closes_at')
	list_editable = ('is_closed', 'opens_at', 'closes_at')
	ordering = ('weekday',)


@admin.register(SalonClosure)
class SalonClosureAdmin(admin.ModelAdmin):
	list_display = ('date', 'reason')
	list_filter = ('date',)
	date_hierarchy = 'date'
	search_fields = ('reason',)

