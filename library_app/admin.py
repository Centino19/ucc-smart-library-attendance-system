from django.contrib import admin
from .models import Patron, AttendanceLog, SystemLog

@admin.register(Patron)
class PatronAdmin(admin.ModelAdmin):
    # Changed 'patron_id' to 'id_number'
    list_display = ('id_number', 'last_name', 'first_name', 'role', 'department')
    search_fields = ('id_number', 'last_name', 'first_name')
    list_filter = ('role', 'department')

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('patron', 'scan_time', 'date_only')
    list_filter = ('date_only', 'patron__department') # Added department filter for easier stats checking!

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'action', 'details')
    list_filter = ('action', 'user')