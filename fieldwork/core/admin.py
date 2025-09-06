from django.contrib import admin
from django import forms
from .models import Customer, Job

class JobAdminForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        input_formats=['%d-%m-%Y %H:%M'],
        widget=forms.DateTimeInput(format='%d-%m-%Y %H:%M')
    )
    end_time = forms.DateTimeField(
        input_formats=['%d-%m-%Y %H:%M'],
        widget=forms.DateTimeInput(format='%d-%m-%Y %H:%M')
    )

    class Meta:
        model = Job
        fields = '__all__'

class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ('customer', 'start_time', 'end_time', 'status', 'recurrence_type', 'recurrence_frequency')
    list_filter = ('status', 'recurrence_type', 'start_time')
    search_fields = ('customer__name', 'description')

admin.site.register(Customer)
admin.site.register(Job, JobAdmin)
