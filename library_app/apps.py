from django.apps import AppConfig
import os
import sys

class LibraryAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library_app'

    def ready(self):
        # 1. Check if we are running via 'runserver' (Development)
        is_runserver = 'runserver' in sys.argv

        # 2. If Dev: Only run in the reloaded process (RUN_MAIN='true') to avoid duplicates
        if is_runserver and os.environ.get('RUN_MAIN', None) != 'true':
            return

        # 3. Prevent scheduler from running during utility commands (migrate, etc.)
        ignore_commands = ['migrate', 'makemigrations', 'collectstatic', 'createsuperuser', 'force_checkout', 'test']
        if any(cmd in sys.argv for cmd in ignore_commands):
            return

        # 4. Start the Scheduler
        self.start_scheduler()

    def start_scheduler(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from django.core.management import call_command
            from django.conf import settings

            def auto_checkout_job():
                print("⏰ Running Scheduled Force Checkout...")
                call_command('force_checkout')

            scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
            scheduler.add_job(auto_checkout_job, 'cron', hour=16, minute=45)
            scheduler.start()
            print(f"✅ Scheduler Started: Auto-Checkout set for 4:45 PM Daily ({settings.TIME_ZONE})")
        except Exception as e:
            print(f"Scheduler Error: {e}")