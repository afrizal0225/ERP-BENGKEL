from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create UserProfile for users who don\'t have one'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        created_count = 0

        for user in users_without_profile:
            UserProfile.objects.create(user=user, employee_id=None)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created UserProfile for user: {user.username}')
            )

        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have UserProfiles')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Created {created_count} UserProfile(s)')
            )