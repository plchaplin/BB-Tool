from django.contrib import admin
from .models import Customer, Job

class JobAdmin(admin.ModelAdmin):
    list_display = ('customer', 'date', 'start_time', 'end_time', 'status', 'recurrence_type', 'recurrence_frequency')
    list_filter = ('status', 'recurrence_type', 'date')
    search_fields = ('customer__name', 'description')

admin.site.register(Customer)
admin.site.register(Job, JobAdmin)
