from datetime import datetime, timedelta

from django.db import migrations
from django.utils import timezone


def create_existing_reservations(apps, schema_editor):
    Appointment = apps.get_model('bookings', 'Appointment')
    BookingSlot = apps.get_model('bookings', 'BookingSlot')
    Service = apps.get_model('salon_services', 'Service')
    database = schema_editor.connection.alias
    tz = timezone.get_current_timezone()

    for appointment in Appointment.objects.using(database).all().iterator():
        service_duration = Service.objects.using(database).filter(
            pk=appointment.service_id
        ).values_list('duration_minutes', flat=True).first() or 60
        appointment.duration_minutes = service_duration
        appointment.save(using=database, update_fields=['duration_minutes'])

        if appointment.status not in ('pending', 'confirmed'):
            continue

        start = timezone.make_aware(
            datetime.combine(appointment.appointment_date, appointment.appointment_time),
            tz,
        )
        BookingSlot.objects.using(database).bulk_create(
            [
                BookingSlot(appointment_id=appointment.pk, starts_at=start + timedelta(minutes=offset))
                for offset in range(0, service_duration, 15)
            ],
            ignore_conflicts=True,
        )


def remove_existing_reservations(apps, schema_editor):
    apps.get_model('bookings', 'BookingSlot').objects.using(
        schema_editor.connection.alias
    ).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('bookings', '0002_appointment_duration_minutes_bookingslot'),
        ('salon_services', '0002_service_duration_minutes'),
    ]

    operations = [
        migrations.RunPython(create_existing_reservations, remove_existing_reservations),
    ]
