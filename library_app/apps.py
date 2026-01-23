from django.apps import AppConfig

class LibraryAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library_app'

    def ready(self):
        # Prevent the scheduler from running twice (common issue with runserver)
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        from . import tasks
        from apscheduler.schedulers.background import BackgroundScheduler

        # 1. Initialize the Scheduler
        scheduler = BackgroundScheduler()

        # 2. Add the Job: Run 'run_auto_checkout' daily at 17:00 (5:00 PM)
        # You can change 'hour=17' to any time you like (24-hour format)
        scheduler.add_job(tasks.run_auto_checkout, 'cron', hour=17, minute=0)

        # 3. Start it
        scheduler.start()
        print("✅ Scheduler Started: Auto-Checkout set for 5:00 PM Daily")