from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from bookings.models import Appointment
from .forms import ServiceForm
from .models import Service


def home(request):
    services = Service.objects.all().order_by('name')[:6]
    return render(request, 'salon_services/home.html', {'services': services})


def service_list(request):
    services = Service.objects.all().order_by('name')
    query = request.GET.get('q', '').strip()
    if query:
        services = services.filter(Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'salon_services/service_list.html', {'services': services, 'query': query})


def staff_required(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
def dashboard(request):
    if request.user.is_staff or request.user.is_superuser:
        appointments = Appointment.objects.select_related('customer', 'service').order_by('appointment_date', 'appointment_time')
        total_appointments = appointments.count()
        pending_count = appointments.filter(status='pending').count()
        confirmed_count = appointments.filter(status='confirmed').count()
        services_count = Service.objects.count()
        return render(request, 'salon_services/dashboard.html', {
            'appointments': appointments[:8], 'total_appointments': total_appointments,
            'pending_count': pending_count, 'confirmed_count': confirmed_count,
            'services_count': services_count, 'is_manager': True,
        })
    appointments = Appointment.objects.filter(customer=request.user).select_related('service').order_by('-appointment_date', '-appointment_time')
    return render(request, 'salon_services/dashboard.html', {'appointments': appointments[:8], 'is_manager': False})


@login_required
@user_passes_test(staff_required)
def service_create(request):
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service added successfully.')
        return redirect('service_list')
    return render(request, 'salon_services/service_form.html', {'form': form, 'heading': 'Add a service'})


@login_required
@user_passes_test(staff_required)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service updated successfully.')
        return redirect('service_list')
    return render(request, 'salon_services/service_form.html', {'form': form, 'heading': 'Edit service'})


@login_required
@user_passes_test(staff_required)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted.')
        return redirect('service_list')
    return render(request, 'salon_services/service_confirm_delete.html', {'service': service})
