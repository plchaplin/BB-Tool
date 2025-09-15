from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Lists all users who have a StaffProfile associated with them.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Attempting to run list_staff command..."))
        self.stdout.write(self.style.SUCCESS("--- Checking for users with a Staff Profile ---"))

        staff_users = User.objects.filter(staffprofile__isnull=False).order_by('username')

        if not staff_users.exists():
            self.stdout.write(self.style.WARNING("No users with a Staff Profile found."))
            self.stdout.write("To make a user appear as 'Staff', you must add a 'Staff Profile' for them in the admin area.")
            return

        self.stdout.write(f"Found {staff_users.count()} staff member(s):")
        for user in staff_users:
            full_name = user.get_full_name()
            self.stdout.write(f"- {user.username} ({full_name})" if full_name else f"- {user.username}")

        self.stdout.write(self.style.SUCCESS("--- Check complete ---"))
