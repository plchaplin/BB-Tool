from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

class Job(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    description = models.TextField()
    address = models.TextField()
    scheduled_time = models.DateTimeField()
    is_repeat_job = models.BooleanField(default=False)

    def __str__(self):
        return f"Job for {self.customer} at {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
