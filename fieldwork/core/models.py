from django.db import models
from django.contrib.auth.models import User

RECURRENCE_TYPE_CHOICES = [
    ('none', 'None'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
]

class Customer(models.Model):
    name = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    town = models.CharField(max_length=255)
    postcode = models.CharField(max_length=10)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    # Default settings for new jobs
    default_duration_minutes = models.IntegerField(default=60, help_text="Default job duration in minutes")
    default_recurrence_type = models.CharField(max_length=20, choices=RECURRENCE_TYPE_CHOICES, default='none')
    default_recurrence_frequency = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class Job(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    JOB_TYPE_CHOICES = [
        ('gardening', 'Gardening'),
        ('landscaping', 'Landscaping'),
        ('maintenance', 'Maintenance'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    staff = models.ManyToManyField(User, related_name='jobs')
    description = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='gardening')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    recurrence_type = models.CharField(
        max_length=20,
        choices=RECURRENCE_TYPE_CHOICES,
        default='none'
    )
    recurrence_frequency = models.PositiveIntegerField(
        default=1,
        help_text="Frequency of recurrence (e.g., for 'weekly' type, a frequency of 2 means every 2 weeks)"
    )

    def __str__(self):
        return f"Job for {self.customer} on {self.date.strftime('%Y-%m-%d')}"

class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staffprofile')
    street = models.CharField(max_length=255, blank=True)
    town = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=10, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    contracted_hours_per_day = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)

    def __str__(self):
        return self.user.username
