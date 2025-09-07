from django.contrib import admin
from django import forms
from .models import Customer, Job
from .widgets import TimeSelectWidget

class JobAdminForm(forms.ModelForm):
    date = forms.DateField(widget=admin.widgets.AdminDateWidget)
    start_time = forms.TimeField(widget=TimeSelectWidget)
    end_time = forms.TimeField(widget=TimeSelectWidget)

    class Meta:
        model = Job
        fields = '__all__'

class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ('customer', 'job_type', 'date', 'start_time', 'end_time', 'status', 'recurrence_type', 'recurrence_frequency')
    list_filter = ('status', 'job_type', 'recurrence_type', 'date')
    search_fields = ('customer__name', 'description')

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'street', 'town', 'postcode', 'phone_number', 'email')
    search_fields = ('name', 'postcode', 'street')

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Job, JobAdmin)
