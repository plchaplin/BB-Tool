import random
from datetime import date, timedelta, datetime
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
            start_time = datetime(today.year, today.month, today.day, start_hour, 0, 0)
            end_time = start_time + timedelta(hours=random.randint(1, 4))

            job = Job.objects.create(
                customer=customer,
                description=fake.text(max_nb_chars=100),
                address=customer.address,
                start_time=start_time,
                end_time=end_time,
                status=random.choice(['scheduled', 'in_progress', 'completed']),
                recurrence=random.choice(['none', 'weekly', 'bi-weekly', 'monthly'])
            )
            job.staff.set(random.sample(staff_users, k=random.randint(1, 3)))


        self.stdout.write(self.style.SUCCESS('Successfully seeded data.'))
