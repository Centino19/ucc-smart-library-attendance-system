from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from library_app.models import AttendanceLog


class Command(BaseCommand):
    help = 'Automatically checks out ANY user who forgot to logout (past or present)'

    def handle(self, *args, **kwargs):
        # 1. Get the current time for the checkout timestamp
        # You can use the current moment, or set a specific static time.
        # Here we use "Now" so the checkout time is accurate to when you ran the script.
        checkout_time = timezone.now()

        # 2. Find ALL logs where checkout is missing (regardless of date)
        # REMOVED: scan_time__date=today
        open_logs = AttendanceLog.objects.filter(time_out__isnull=True)

        count = open_logs.count()

        if count > 0:
            # 3. Update them all
            open_logs.update(time_out=checkout_time)

            self.stdout.write(self.style.SUCCESS(f'Successfully closed {count} stale sessions.'))
        else:
            self.stdout.write(self.style.WARNING('No active sessions found.'))