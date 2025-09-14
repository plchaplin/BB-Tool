from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Customer, Job, StaffProfile, JobLog
from .widgets import TimeSelectWidget
from django.utils.translation import gettext_lazy as _
import json
from datetime import datetime, timedelta, date

# Define an inline admin descriptor for StaffProfile model
# which acts a bit like a singleton
class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fields = ('phone_number',
              ('hours_monday', 'hours_tuesday', 'hours_wednesday', 'hours_thursday',
               'hours_friday', 'hours_saturday', 'hours_sunday'))


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (StaffProfileInline,)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


def get_duration_choices():
    """Generates a list of duration choices in 30-minute increments up to 8 hours."""
    choices = []
    for minutes in range(30, 8 * 60 + 1, 30):
        hours = minutes / 60
        if hours == 1.0:
            label = "1 hour"
        elif hours.is_integer():
            label = f"{int(hours)} hours"
        else:
            label = f"{hours} hours"
        choices.append((minutes, label))
    return choices


class JobAdminForm(forms.ModelForm):
    duration = forms.TypedChoiceField(
        choices=get_duration_choices,
        coerce=int,
        help_text="The job will be scheduled for this duration from the start time."
    )

    class Meta:
        model = Job
        fields = ['customer', 'job_type', 'description', 'staff', 'date',
                  'start_time', 'duration', 'status', 'recurrence_type',
                  'recurrence_frequency']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

        # Add all customer durations as a data attribute for our JS to use
        customers = Customer.objects.all()
        customer_durations = {c.id: c.default_duration_minutes for c in customers}
        self.fields['customer'].widget.attrs['data-durations'] = json.dumps(customer_durations)

        # If editing an existing job, calculate its duration and set it as the initial value
        if instance and instance.pk and instance.start_time and instance.end_time:
            start_dt = datetime.combine(date.min, instance.start_time)
            end_dt = datetime.combine(date.min, instance.end_time)
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
            self.initial['duration'] = int(duration_minutes)
        # For new jobs, the initial duration can be set by JS when a customer is selected


class JobLogInline(admin.TabularInline):
    model = JobLog
    extra = 1
    fields = ('timestamp', 'author', 'note')
    readonly_fields = ('timestamp', 'author')
    can_delete = False


class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ('customer', 'job_type', 'date', 'start_time', 'get_assigned_staff', 'status')
    list_filter = ('status', 'job_type', 'date', 'customer', 'staff')
    search_fields = ('customer__name', 'description')
    inlines = [JobLogInline]

    class Media:
        js = ("core/js/job_admin.js",)

    def get_assigned_staff(self, obj):
        return ", ".join([s.get_full_name() or s.username for s in obj.staff.all()])
    get_assigned_staff.short_description = 'Assigned Staff'

    def save_model(self, request, obj, form, change):
        # Calculate end_time from duration before saving
        start_time = form.cleaned_data.get('start_time')
        duration = form.cleaned_data.get('duration')

        if start_time and duration:
            start_datetime = datetime.combine(obj.date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)
            obj.end_time = end_datetime.time()

        # Apply customer default for recurrence on new jobs
        if not change and obj.customer:
            if 'recurrence_type' not in form.changed_data and obj.customer.default_recurrence_type != 'none':
                obj.recurrence_type = obj.customer.default_recurrence_type
                obj.recurrence_frequency = obj.customer.default_recurrence_frequency

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, JobLog) and not instance.pk:
                instance.author = request.user
            instance.save()
        formset.save_m2m()


class CustomerAdminForm(forms.ModelForm):
    default_duration_minutes = forms.TypedChoiceField(
        choices=get_duration_choices,
        coerce=int,
        label="Default duration"
    )

    class Meta:
        model = Customer
        fields = '__all__'


class CustomerAdmin(admin.ModelAdmin):
    form = CustomerAdminForm
    list_display = ('name', 'town', 'postcode', 'hourly_rate', 'default_duration_minutes', 'default_recurrence_type')
    search_fields = ('name', 'postcode', 'street')
    fieldsets = (
        ('Contact Info', {
            'fields': ('name', 'phone_number', 'email')
        }),
        ('Address', {
            'fields': ('street', 'town', 'postcode')
        }),
        ('Job & Billing Defaults', {
            'fields': ('hourly_rate', 'default_duration_minutes', 'default_recurrence_type', 'default_recurrence_frequency')
        }),
        ('Scheduling Constraints', {
            'fields': ('day_constraint_type',
                       ('can_visit_monday', 'can_visit_tuesday', 'can_visit_wednesday',
                        'can_visit_thursday', 'can_visit_friday', 'can_visit_saturday',
                        'can_visit_sunday'))
        }),
    )

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Job, JobAdmin)
