from django.db import models
from django.utils import timezone


class Patron(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('guest', 'Guest'),
    ]

    DEPARTMENT_CHOICES = [
        ('SBS', 'School of Business Sciences (SBS)'),
        ('SEAS', 'School of Education, Arts, and Sciences (SEAS)'),
        ('SHES', 'School of Health and Education Sciences (SHES)'),
        ('BES', 'Basic Education School (BES)'),
        ('GS', 'Graduate School'),
    ]

    # Core Identity
    id_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, blank=True, null=True)  # Added for QR Emailing

    # Classification
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, null=True, blank=True)

    # Academic Details (Nullable to support Guests/Faculty/BES)
    program = models.CharField(max_length=100, blank=True, null=True)
    major = models.CharField(max_length=100, blank=True, null=True)  # Added for specific tracks
    year_level = models.CharField(max_length=50, blank=True, null=True)

    # System Fields
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id_number} - {self.last_name}"


class AttendanceLog(models.Model):
    patron = models.ForeignKey(Patron, on_delete=models.CASCADE, related_name='logs')

    # Time In
    scan_time = models.DateTimeField(default=timezone.now)

    # Time Out (Blank until they scan out)
    time_out = models.DateTimeField(blank=True, null=True)

    # Helper for filtering stats
    date_only = models.DateField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-scan_time']

    def __str__(self):
        return f"{self.patron.last_name} - {self.scan_time}"