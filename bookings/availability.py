from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import BookingSlot, SalonClosure, WeeklySchedule

SLOT_MINUTES = 15
OPENING_TIME = time(9, 0)
CLOSING_TIME = time(18, 0)
ACTIVE_STATUSES = ('pending', 'confirmed')


def slot_datetimes(day, start_time, duration_minutes):
    """Return the quarter-hour reservation timestamps for a service booking."""
    tz = timezone.get_current_timezone()
    start = timezone.make_aware(datetime.combine(day, start_time), tz)
    return [
        start + timedelta(minutes=offset)
        for offset in range(0, duration_minutes, SLOT_MINUTES)
    ]


def available_start_times(day, service):
    """List open quarter-hour start times that fit the service's full duration."""
    if not day or not service:
        return []

    if SalonClosure.objects.filter(date=day).exists():
        return []

    schedule = WeeklySchedule.objects.filter(weekday=day.weekday()).first()
    if schedule:
        if schedule.is_closed:
            return []
        opening_time = schedule.opens_at
        closing_time = schedule.closes_at
    else:
        opening_time = OPENING_TIME
        closing_time = CLOSING_TIME

    tz = timezone.get_current_timezone()
    day_start = timezone.make_aware(datetime.combine(day, time.min), tz)
    day_end = day_start + timedelta(days=1)
    reserved = {
        timezone.localtime(starts_at, tz)
        for starts_at in BookingSlot.objects.filter(
            starts_at__gte=day_start,
            starts_at__lt=day_end,
            appointment__status__in=ACTIVE_STATUSES,
        ).values_list('starts_at', flat=True)
    }

    latest_start = (
        datetime.combine(day, closing_time)
        - timedelta(minutes=service.duration_minutes)
    ).time()
    candidate = datetime.combine(day, opening_time)
    latest = datetime.combine(day, latest_start)
    now = timezone.localtime()
    results = []

    while candidate <= latest:
        start_time = candidate.time()
        start_datetime = timezone.make_aware(candidate, tz)
        blocks = slot_datetimes(day, start_time, service.duration_minutes)
        if start_datetime > now and not any(block in reserved for block in blocks):
            results.append(start_time)
        candidate += timedelta(minutes=SLOT_MINUTES)

    return results


def reserve_appointment_slots(appointment):
    """Persist the appointment's occupied blocks; the unique timestamp is race-safe."""
    BookingSlot.objects.bulk_create([
        BookingSlot(appointment=appointment, starts_at=starts_at)
        for starts_at in slot_datetimes(
            appointment.appointment_date,
            appointment.appointment_time,
            appointment.duration_minutes,
        )
    ])
