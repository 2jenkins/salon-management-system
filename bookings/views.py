from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from .availability import ACTIVE_STATUSES, available_start_times, reserve_appointment_slots
from .forms import AppointmentForm
from .models import Appointment, SalonClosure, WeeklySchedule


def staff_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
def book_appointment(request):
    initial = {
        'service': request.GET.get('service'),
        'appointment_date': request.GET.get('appointment_date'),
    }
    form = AppointmentForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                appointment = form.save(commit=False)
                appointment.customer = request.user
                appointment.duration_minutes = appointment.service.duration_minutes
                appointment.save()
                reserve_appointment_slots(appointment)
        except IntegrityError:
            form.add_error(None, 'That time was just booked. Please choose another available time.')
            return render(request, 'bookings/appointment_form.html', {'form': form})
        messages.success(request, 'Appointment requested. You can track its status from your dashboard.')
        return redirect('dashboard')
    return render(request, 'bookings/appointment_form.html', {'form': form})


@login_required
def available_appointment_slots(request):
    service_id = request.GET.get('service')
    day = parse_date(request.GET.get('date', ''))
    if not day or not service_id:
        return JsonResponse({'slots': []})
    from salon_services.models import Service

    try:
        service = Service.objects.get(pk=service_id)
    except (Service.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'slots': []})

    closure = SalonClosure.objects.filter(date=day).first()
    schedule = WeeklySchedule.objects.filter(weekday=day.weekday()).first()
    if closure:
        notice = f'The salon is closed on this date{": " + closure.reason if closure.reason else "."}'
    elif schedule and schedule.is_closed:
        notice = f'The salon is closed on {schedule.get_weekday_display()}.'
    else:
        notice = ''

    return JsonResponse({
        'notice': notice,
        'slots': [
            {'value': value.strftime('%H:%M'), 'label': value.strftime('%I:%M %p').lstrip('0')}
            for value in available_start_times(day, service)
        ]
    })


@login_required
def appointment_list(request):
    appointments = Appointment.objects.select_related('customer', 'service')
    if not (request.user.is_staff or request.user.is_superuser):
        appointments = appointments.filter(customer=request.user)
    return render(request, 'bookings/appointment_list.html', {'appointments': appointments.order_by('-appointment_date', '-appointment_time')})


@login_required
def cancel_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.customer_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method == 'POST' and appointment.status in ('pending', 'confirmed'):
        with transaction.atomic():
            appointment.status = 'cancelled'
            appointment.save(update_fields=['status'])
            appointment.reserved_slots.all().delete()
        messages.success(request, 'Appointment cancelled.')
    return redirect('appointment_list')


@login_required
@user_passes_test(staff_required)
def update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Appointment.STATUS_CHOICES):
            try:
                with transaction.atomic():
                    appointment = Appointment.objects.select_for_update().get(pk=appointment.pk)
                    was_active = appointment.status in ACTIVE_STATUSES
                    appointment.status = status
                    appointment.save(update_fields=['status'])
                    if status in ACTIVE_STATUSES and not was_active:
                        reserve_appointment_slots(appointment)
                    elif status not in ACTIVE_STATUSES:
                        appointment.reserved_slots.all().delete()
                messages.success(request, 'Appointment status updated.')
            except IntegrityError:
                messages.error(request, 'That time conflicts with another booking; the status was not changed.')
    return redirect('appointment_list')
