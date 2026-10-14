from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from salon_services.models import Service


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.service}"


class BookingSlot(models.Model):
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='reserved_slots',
    )
    starts_at = models.DateTimeField(unique=True)

    class Meta:
        ordering = ('starts_at',)

    def __str__(self):
        return f"{self.appointment} at {self.starts_at}"


class WeeklySchedule(models.Model):
    WEEKDAYS = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    weekday = models.PositiveSmallIntegerField(choices=WEEKDAYS, unique=True)
    is_closed = models.BooleanField(default=False)
    opens_at = models.TimeField(default='09:00')
    closes_at = models.TimeField(default='18:00')

    class Meta:
        ordering = ('weekday',)
        verbose_name = 'weekly opening hours'
        verbose_name_plural = 'weekly opening hours'

    def clean(self):
        super().clean()
        if not self.is_closed and self.opens_at and self.closes_at and self.opens_at >= self.closes_at:
            raise ValidationError({'closes_at': 'Closing time must be later than opening time.'})
        if not self.is_closed and self.opens_at and self.closes_at:
            if self.opens_at.minute % 15 or self.closes_at.minute % 15:
                raise ValidationError('Opening and closing times must use 15-minute increments.')

    def __str__(self):
        if self.is_closed:
            return f'{self.get_weekday_display()}: closed'
        return f'{self.get_weekday_display()}: {self.opens_at:%H:%M}–{self.closes_at:%H:%M}'


class SalonClosure(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ('date',)
        verbose_name = 'closed date'
        verbose_name_plural = 'closed dates'

    def clean(self):
        super().clean()
        if self.date and Appointment.objects.filter(
            appointment_date=self.date,
            status__in=('pending', 'confirmed'),
        ).exists():
            raise ValidationError({'date': 'There are active appointments on this date. Reschedule or cancel them before closing the salon.'})

    def __str__(self):
        return f'{self.date:%b %d, %Y}' + (f' — {self.reason}' if self.reason else '')

