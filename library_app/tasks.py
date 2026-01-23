from django.core.management import call_command

def run_auto_checkout():
    """
    This function triggers your existing 'auto_checkout' management command.
    """
    print("⏰ 5:00 PM Scheduler: Running Auto-Checkout Command...")
    # This simulates typing "python manage.py auto_checkout" in the terminal
    call_command('force_checkout')