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
                is_staff=True
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
                street=fake.street_address(),
                town=fake.city(),
                postcode=fake.postcode(),
                phone_number=fake.phone_number(),
                email=fake.email()
            )
            customers.append(customer)

        # Create jobs for the next 14 days
        today = date.today()
        for day_offset in range(14):
            job_date = today + timedelta(days=day_offset)
            # Create a random number of jobs for each day
            for _ in range(random.randint(2, 5)):
                customer = random.choice(customers)
                start_hour = random.randint(8, 16)
                start_minute = random.choice([0, 15, 30, 45])
                start_time_obj = time(start_hour, start_minute)

                # Duration in 15-minute increments, from 1 to 4 hours
                duration_in_minutes = random.randint(4, 16) * 15
                start_datetime = datetime.combine(job_date, start_time_obj)
                end_datetime = start_datetime + timedelta(minutes=duration_in_minutes)

                # Skip jobs that span midnight
                if end_datetime.date() > job_date:
                    continue

                end_time_obj = end_datetime.time()

                recurrence_type = random.choice(['none', 'weekly', 'monthly'])
            recurrence_frequency = 1
            if recurrence_type == 'weekly':
                recurrence_frequency = random.randint(1, 4)

            job = Job.objects.create(
                customer=customer,
                description=fake.text(max_nb_chars=100),
                job_type=random.choice([choice[0] for choice in Job.JOB_TYPE_CHOICES]),
                date=job_date,
                start_time=start_time_obj,
                end_time=end_time_obj,
                status=random.choice(['scheduled', 'in_progress', 'completed']),
                recurrence_type=recurrence_type,
                recurrence_frequency=recurrence_frequency
            )
            job.staff.set(random.sample(staff_users, k=random.randint(1, 3)))

        # Create overlapping jobs for one staff member for testing
        if staff_users and customers:
            test_staff = staff_users[0]
            test_customer = customers[0]
            test_date = date.today() + timedelta(days=2)

            # Job 1
            job1 = Job.objects.create(
                customer=test_customer,
                description="Overlapping Job 1",
                job_type='gardening',
                date=test_date,
                start_time=time(9, 0),
                end_time=time(11, 0),
                status='scheduled'
            )
            job1.staff.set([test_staff])

            # Job 2 (overlaps with Job 1)
            job2 = Job.objects.create(
                customer=customers[1],
                description="Overlapping Job 2",
                job_type='maintenance',
                date=test_date,
                start_time=time(10, 0),
                end_time=time(12, 0),
                status='scheduled'
            )
            job2.staff.set([test_staff])

        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))
