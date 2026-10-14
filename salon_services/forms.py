from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['duration_minutes'].min_value = 15
        self.fields['duration_minutes'].max_value = 360
        self.fields['duration_minutes'].help_text = 'Service length in minutes, in 15-minute increments.'
        for field in self.fields.values():
            if field.widget.__class__.__name__ not in ('ClearableFileInput',):
                field.widget.attrs.setdefault('class', 'form-control')

    class Meta:
        model = Service
        fields = ('name', 'description', 'price', 'duration_minutes', 'image')
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def clean_duration_minutes(self):
        duration = self.cleaned_data['duration_minutes']
        if duration % 15:
            raise forms.ValidationError('Duration must use 15-minute increments.')
        return duration
