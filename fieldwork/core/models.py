from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    staff = models.ManyToManyField(User, related_name='jobs')
    description = models.TextField()
    address = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    RECURRENCE_TYPE_CHOICES = [
        ('none', 'None'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
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
        return f"Job for {self.customer} on {self.start_time.strftime('%Y-%m-%d')}"
