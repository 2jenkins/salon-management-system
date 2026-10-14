from datetime import time, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from bookings.availability import reserve_appointment_slots
from bookings.forms import AppointmentForm
from bookings.models import Appointment, BookingSlot, SalonClosure, WeeklySchedule
from salon_services.models import Service
from users.models import CustomUser


class AppointmentFormTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='client',
            email='client@example.com',
            password='StrongPass123!',
        )
        self.service = Service.objects.create(
            name='Haircut',
            description='Standard cut',
            price='45.00',
            duration_minutes=60,
        )

    def test_future_booking_is_valid(self):
        future_date = (timezone.localdate() + timedelta(days=2)).isoformat()
        form = AppointmentForm(
            data={
                'service': self.service.pk,
                'appointment_date': future_date,
                'appointment_time': '10:00',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_past_date_is_rejected(self):
        form = AppointmentForm(
            data={
                'service': self.service.pk,
                'appointment_date': (timezone.localdate() - timedelta(days=1)).isoformat(),
                'appointment_time': '10:00',
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('Please choose today or a future date.', form.errors['appointment_date'])

    def test_availability_excludes_overlapping_appointments(self):
        self.client.force_login(self.user)
        day = timezone.localdate() + timedelta(days=2)
        appointment = Appointment.objects.create(
            customer=self.user,
            service=self.service,
            appointment_date=day,
            appointment_time=time(10, 0),
            duration_minutes=60,
        )
        reserve_appointment_slots(appointment)

        response = self.client.get(
            reverse('available_appointment_slots'),
            {'service': self.service.pk, 'date': day.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        available = {slot['value'] for slot in response.json()['slots']}
        self.assertIn('09:00', available)
        self.assertNotIn('09:15', available)
        self.assertNotIn('10:00', available)
        self.assertIn('11:00', available)

        shorter_service = Service.objects.create(
            name='Quick trim',
            description='A short service',
            price='20.00',
            duration_minutes=30,
        )
        shorter_service_slots = self.client.get(
            reverse('available_appointment_slots'),
            {'service': shorter_service.pk, 'date': day.isoformat()},
        ).json()['slots']
        shorter_available = {slot['value'] for slot in shorter_service_slots}
        self.assertNotIn('09:45', shorter_available)
        self.assertIn('11:00', shorter_available)

    def test_database_rejects_overlapping_reservation_blocks(self):
        day = timezone.localdate() + timedelta(days=2)
        first = Appointment.objects.create(
            customer=self.user,
            service=self.service,
            appointment_date=day,
            appointment_time=time(10, 0),
            duration_minutes=60,
        )
        second_service = Service.objects.create(
            name='Quick trim',
            description='A short service',
            price='20.00',
            duration_minutes=30,
        )
        second = Appointment.objects.create(
            customer=self.user,
            service=second_service,
            appointment_date=day,
            appointment_time=time(10, 15),
            duration_minutes=30,
        )
        reserve_appointment_slots(first)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                reserve_appointment_slots(second)

    def test_available_times_follow_custom_weekday_hours(self):
        day = timezone.localdate() + timedelta(days=2)
        WeeklySchedule.objects.filter(weekday=day.weekday()).update(
            opens_at=time(10, 0),
            closes_at=time(12, 0),
            is_closed=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('available_appointment_slots'),
            {'service': self.service.pk, 'date': day.isoformat()},
        )

        available = {slot['value'] for slot in response.json()['slots']}
        self.assertEqual(available, {'10:00', '10:15', '10:30', '10:45', '11:00'})

    def test_closed_weekday_has_no_available_times(self):
        day = timezone.localdate() + timedelta(days=2)
        WeeklySchedule.objects.filter(weekday=day.weekday()).update(is_closed=True)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('available_appointment_slots'),
            {'service': self.service.pk, 'date': day.isoformat()},
        )

        self.assertEqual(response.json()['slots'], [])
        self.assertIn('salon is closed', response.json()['notice'])

    def test_one_off_closure_has_no_available_times_and_shows_reason(self):
        day = timezone.localdate() + timedelta(days=2)
        SalonClosure.objects.create(date=day, reason='Public holiday')
        self.client.force_login(self.user)

        response = self.client.get(
            reverse('available_appointment_slots'),
            {'service': self.service.pk, 'date': day.isoformat()},
        )

        self.assertEqual(response.json()['slots'], [])
        self.assertIn('Public holiday', response.json()['notice'])

    def test_booking_reserves_all_quarter_hour_blocks(self):
        self.client.force_login(self.user)
        day = timezone.localdate() + timedelta(days=2)

        response = self.client.post(
            reverse('book_appointment'),
            {
                'service': self.service.pk,
                'appointment_date': day.isoformat(),
                'appointment_time': '10:00',
            },
        )

        self.assertRedirects(response, reverse('dashboard'))
        appointment = Appointment.objects.get(customer=self.user)
        self.assertEqual(appointment.duration_minutes, 60)
        self.assertEqual(BookingSlot.objects.filter(appointment=appointment).count(), 4)

    def test_cancelling_booking_makes_its_time_available_again(self):
        self.client.force_login(self.user)
        day = timezone.localdate() + timedelta(days=2)
        appointment = Appointment.objects.create(
            customer=self.user,
            service=self.service,
            appointment_date=day,
            appointment_time=time(10, 0),
            duration_minutes=60,
        )
        reserve_appointment_slots(appointment)

        response = self.client.post(reverse('cancel_appointment', args=[appointment.pk]))

        self.assertRedirects(response, reverse('appointment_list'))
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, 'cancelled')
        self.assertFalse(BookingSlot.objects.filter(appointment=appointment).exists())
        available = self.client.get(
            reverse('available_appointment_slots'),
            {'service': self.service.pk, 'date': day.isoformat()},
        ).json()['slots']
        self.assertIn('10:00', {slot['value'] for slot in available})

# Create your tests here.
