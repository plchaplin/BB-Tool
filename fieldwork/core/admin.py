from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Customer, Job, StaffProfile, JobLog
from .widgets import TimeSelectWidget

# Define an inline admin descriptor for StaffProfile model
# which acts a bit like a singleton
class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name_plural = 'profile'
    fields = ('phone_number',
              ('hours_monday', 'hours_tuesday', 'hours_wednesday', 'hours_thursday',
               'hours_friday', 'hours_saturday', 'hours_sunday'))

from django.utils.translation import gettext_lazy as _


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


import json
from datetime import datetime, timedelta

class JobAdminForm(forms.ModelForm):
    date = forms.DateField(widget=admin.widgets.AdminDateWidget)
    start_time = forms.TimeField(widget=TimeSelectWidget)
    end_time = forms.TimeField(widget=TimeSelectWidget, required=False)

    class Meta:
        model = Job
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add all customer durations as a data attribute for our JS to use
        customers = Customer.objects.all()
        customer_durations = {c.id: c.default_duration_minutes for c in customers}
        self.fields['customer'].widget.attrs['data-durations'] = json.dumps(customer_durations)

        instance = kwargs.get('instance')
        # On the change form, show the customer's defaults as help text
        if instance and instance.pk and instance.customer:
            customer = instance.customer
            self.fields['recurrence_type'].help_text = (
                f"Customer default: <b>{customer.get_default_recurrence_type_display()}</b>"
            )
            self.fields['recurrence_frequency'].help_text = (
                f"Customer default: <b>{customer.default_recurrence_frequency}</b>"
            )
            if customer.default_duration_minutes:
                self.fields['end_time'].help_text = (
                    f"Customer default duration: <b>{customer.default_duration_minutes} minutes</b>. "
                    f"Leave blank or unchanged to use this default."
                )
        # On the add form, give a generic hint
        elif not (instance and instance.pk):
            self.fields['customer'].help_text = (
                "Select a customer to have their defaults applied to this job upon saving."
            )

class JobLogInline(admin.TabularInline):
    model = JobLog
    extra = 1
    fields = ('timestamp', 'author', 'note')
    readonly_fields = ('timestamp', 'author')
    can_delete = False


class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ('customer', 'job_type', 'date', 'start_time', 'end_time', 'get_assigned_staff', 'status')
    list_filter = ('status', 'job_type', 'date', 'customer', 'staff')
    search_fields = ('customer__name', 'description')
    inlines = [JobLogInline]

    class Media:
        js = ("core/js/job_admin.js",)

    def get_assigned_staff(self, obj):
        return ", ".join([s.get_full_name() or s.username for s in obj.staff.all()])
    get_assigned_staff.short_description = 'Assigned Staff'

    def save_model(self, request, obj, form, change):
        # If creating a new job, apply customer defaults for fields the user hasn't touched.
        if not change and obj.customer:
            customer = obj.customer

            # Apply default recurrence if the user hasn't changed the recurrence field
            if 'recurrence_type' not in form.changed_data and customer.default_recurrence_type != 'none':
                obj.recurrence_type = customer.default_recurrence_type
                obj.recurrence_frequency = customer.default_recurrence_frequency

            # Apply default duration if end_time is not set and start_time is set
            if 'end_time' not in form.changed_data and obj.start_time:
                if customer.default_duration_minutes:
                    start_datetime = datetime.combine(obj.date, obj.start_time)
                    end_datetime = start_datetime + timedelta(minutes=customer.default_duration_minutes)
                    obj.end_time = end_datetime.time()

        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, JobLog) and not instance.pk:
                instance.author = request.user
            instance.save()
        formset.save_m2m()

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
