from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.utils import timezone

from salon_services.models import Service

from .availability import available_start_times
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    appointment_time = forms.TypedChoiceField(
        choices=(),
        coerce=lambda value: datetime.strptime(value, '%H:%M').time(),
        empty_value=None,
        label='Available time',
    )

    class Meta:
        model = Appointment
        fields = ('service', 'appointment_date', 'appointment_time')
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.localdate().isoformat()}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        service_id = self.data.get('service') or self.initial.get('service')
        appointment_day = self.data.get('appointment_date') or self.initial.get('appointment_date')
        try:
            service = Service.objects.get(pk=service_id)
        except (Service.DoesNotExist, ValueError, TypeError):
            service = None
        if isinstance(appointment_day, str):
            appointment_day = parse_date(appointment_day)
        times = available_start_times(appointment_day, service) if appointment_day and service else []
        self.fields['appointment_time'].choices = [
            ('', 'Choose a service and date first' if not (appointment_day and service) else 'No times available')
        ] + [
            (value.strftime('%H:%M'), value.strftime('%I:%M %p').lstrip('0'))
            for value in times
        ]
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

    def clean_appointment_date(self):
        day = self.cleaned_data['appointment_date']
        if day < timezone.localdate():
            raise forms.ValidationError('Please choose today or a future date.')
        return day

    def clean(self):
        cleaned = super().clean()
        day = cleaned.get('appointment_date')
        time = cleaned.get('appointment_time')
        service = cleaned.get('service')
        if day and time:
            if day < timezone.localdate():
                raise forms.ValidationError('Please choose today or a future date.')
            if day == timezone.localdate() and time <= timezone.localtime().time().replace(second=0, microsecond=0):
                raise forms.ValidationError('Please choose a future time.')
            if service and time not in available_start_times(day, service):
                raise ValidationError('That time is no longer available. Please select another slot.')
        return cleaned
