import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from core.models import Customer, Job

class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')
        fake = Faker()

        # Clean up existing data
        User.objects.filter(is_superuser=False).delete()
        Customer.objects.all().delete()
        Job.objects.all().delete()

        # Create staff users
        staff_users = []
        for _ in range(5):
            username = fake.user_name()
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.email()
            password = 'password'
            user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            user.set_password('password')
            user.last_login = timezone.now()
            user.save()
            staff_users.append(user)

        # Create customers
        customers = []
        for _ in range(20):
            customer = Customer.objects.create(
                name=fake.company(),
                address=fake.address(),
                phone_number=fake.phone_number(),
                email=fake.email()
            )
            customers.append(customer)

        # Create jobs for today
        today = date.today()
        for _ in range(15):
            customer = random.choice(customers)
            start_hour = random.randint(8, 16)
            start_minute = random.choice([0, 15, 30, 45])
            start_time_obj = time(start_hour, start_minute)

            # Duration in 15-minute increments, from 1 to 4 hours
            duration_in_minutes = random.randint(4, 16) * 15
            # We need a datetime object to do timedelta calculations
            start_datetime = datetime.combine(today, start_time_obj)
            end_datetime = start_datetime + timedelta(minutes=duration_in_minutes)
            end_time_obj = end_datetime.time()

            # Handle jobs that cross midnight by moving them to the next day
            job_date = today
            if end_datetime.date() > today:
                # This is a simple approach; for now, we just don't create jobs that span midnight
                # to strictly adhere to the "same day" rule.
                # A more complex approach could be to adjust the end time to 23:59.
                # Let's just skip these for the seeder.
                continue

            recurrence_type = random.choice(['none', 'weekly', 'monthly'])
            recurrence_frequency = 1
            if recurrence_type == 'weekly':
                recurrence_frequency = random.randint(1, 4)

            job = Job.objects.create(
                customer=customer,
                description=fake.text(max_nb_chars=100),
                address=customer.address,
                date=job_date,
                start_time=start_time_obj,
                end_time=end_time_obj,
                status=random.choice(['scheduled', 'in_progress', 'completed']),
                recurrence_type=recurrence_type,
                recurrence_frequency=recurrence_frequency
            )
            job.staff.set(random.sample(staff_users, k=random.randint(1, 3)))


        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))
