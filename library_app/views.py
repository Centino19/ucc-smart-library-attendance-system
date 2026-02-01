import json
import qrcode
import uuid
import calendar
import datetime
from io import BytesIO
import os
import csv
from datetime import timedelta

# Django Imports
from django.db.models import Count, Sum, F, Q, Prefetch
from django.db.models.functions import ExtractMonth, ExtractDay
from django.template.loader import get_template
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator

# Third-party
from xhtml2pdf import pisa

# Local Imports
from .models import Patron, AttendanceLog


# ==========================================
# 1. CORE PAGES (Landing & Dashboard)
# ==========================================

def landing_page(request):
    """Renders the main scan page."""
    return render(request, 'library_app/landing_page.html')


# In views.py

@login_required(login_url='login')
def dashboard(request):
    local_now = timezone.localtime(timezone.now())
    today = local_now.date()
    current_year = today.year

    # ... [Keep your existing Stats, Filters, and Chart Logic here] ...
    # (Lines 1-60 remain the same, I will focus on the Top 5 Logic below)

    # 1. Basic Stats
    daily_count = AttendanceLog.objects.filter(scan_time__date=today).count()
    checked_in_count = AttendanceLog.objects.filter(scan_time__date=today, time_out__isnull=True).count()
    checked_out_count = AttendanceLog.objects.filter(scan_time__date=today, time_out__isnull=False).count()

    selected_dept = request.GET.get('department')
    selected_year = int(request.GET.get('year', current_year))
    selected_month = request.GET.get('month')

    # --- CHART LOGIC ---
    chart_query = AttendanceLog.objects.filter(scan_time__year=selected_year)
    if selected_dept:
        chart_query = chart_query.filter(patron__department=selected_dept)

    chart_labels = []
    chart_data = []

    if selected_month and selected_month != "":
        selected_month = int(selected_month)
        chart_query = chart_query.filter(scan_time__month=selected_month)
        daily_data = chart_query.annotate(day=ExtractDay('scan_time')).values('day').annotate(
            count=Count('id')).order_by('day')
        _, num_days = calendar.monthrange(selected_year, selected_month)
        chart_labels = [str(i) for i in range(1, num_days + 1)]
        chart_data = [0] * num_days
        for entry in daily_data:
            chart_data[entry['day'] - 1] = entry['count']
    else:
        monthly_data = chart_query.annotate(month=ExtractMonth('scan_time')).values('month').annotate(
            count=Count('id')).order_by('month')
        chart_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        chart_data = [0] * 12
        for entry in monthly_data:
            chart_data[entry['month'] - 1] = entry['count']

    # --- PIE CHART LOGIC ---
    dept_stats = AttendanceLog.objects.values('patron__department').annotate(count=Count('id')).order_by('-count')
    pie_labels = [item['patron__department'] for item in dept_stats]
    pie_data = [item['count'] for item in dept_stats]

    # --- TOP 5 VISITORS (Frequency) ---
    # UPDATED: Fetching 'patron__department' instead of program
    top_visits = AttendanceLog.objects.values(
        'patron__first_name', 'patron__last_name', 'patron__department'
    ).annotate(visit_count=Count('id')).order_by('-visit_count')[:5]

    # --- TOP 5 STUDY LEADERS (Time Spent) ---
    # UPDATED: Storing Department alongside Name
    logs_with_duration = AttendanceLog.objects.filter(time_out__isnull=False)
    time_leaderboard = {}

    for log in logs_with_duration:
        duration = log.time_out - log.scan_time
        # Key is now a tuple: (Name, Department) to ensure we capture both
        key = (f"{log.patron.first_name} {log.patron.last_name}", log.patron.department)

        if key in time_leaderboard:
            time_leaderboard[key] += duration
        else:
            time_leaderboard[key] = duration

    sorted_time = sorted(time_leaderboard.items(), key=lambda x: x[1], reverse=True)[:5]
    top_time_spent = []

    for (name, dept), duration in sorted_time:
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        top_time_spent.append({
            'name': name,
            'dept': dept,  # Passing department to template
            'time_str': f"{hours}h {minutes}m"
        })

    # --- RECENT ACTIVITY ---
    today_logs = AttendanceLog.objects.filter(scan_time__date=today).select_related('patron')
    activity_feed = []

    for log in today_logs:
        activity_feed.append({
            'patron': log.patron,
            'role': log.patron.role,
            'status': 'IN',
            'time': log.scan_time
        })
        if log.time_out:
            activity_feed.append({
                'patron': log.patron,
                'role': log.patron.role,
                'status': 'OUT',
                'time': log.time_out
            })

    activity_feed.sort(key=lambda x: x['time'], reverse=True)
    recent_logs = activity_feed[:5]  # Limit to 5

    context = {
        'daily_count': daily_count,
        'checked_in_count': checked_in_count,
        'checked_out_count': checked_out_count,
        'recent_logs': recent_logs,
        'departments': Patron.DEPARTMENT_CHOICES,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'top_visits': top_visits,
        'top_time_spent': top_time_spent,
        'selected_dept': selected_dept,
        'selected_year': selected_year,
        'selected_month': int(selected_month) if selected_month else "",
        'current_year': current_year,
        # New version: Creates a list like [(1, 'January'), (2, 'February')...]
        'month_choices': [(i, calendar.month_name[i]) for i in range(1, 13)],    }
    return render(request, 'library_app/dashboard.html', context)

# ==========================================
# 2. PATRON MANAGEMENT (CRUD)
# ==========================================

@login_required
def patron_list(request):
    """Displays list of users with search and filter options."""
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role')
    dept_filter = request.GET.get('department')
    program_filter = request.GET.get('program')
    year_filter = request.GET.get('year_level')

    patrons = Patron.objects.prefetch_related(
        Prefetch('logs', queryset=AttendanceLog.objects.order_by('-scan_time'))
    ).order_by('-created_at')

    if query:
        # Split the query into individual terms (e.g., "Vincent Faustino" -> ["Vincent", "Faustino"])
        terms = query.split()
        
        # Create a base Q object that matches everything initially
        search_filter = Q()

        # For each term, we want to ensure it appears in AT LEAST ONE of the fields.
        # But since we want ALL terms to be present (AND logic between terms),
        # we combine them iteratively.
        
        # Logic: (Term1 in First OR Term1 in Last OR ...) AND (Term2 in First OR Term2 in Last OR ...)
        
        for term in terms:
            term_filter = (
                Q(first_name__icontains=term) |
                Q(middle_name__icontains=term) |
                Q(last_name__icontains=term) |
                Q(id_number__icontains=term)
            )
            # Combine with AND
            if search_filter == Q():
                search_filter = term_filter
            else:
                search_filter &= term_filter
        
        patrons = patrons.filter(search_filter)

    if role_filter:
        patrons = patrons.filter(role=role_filter)

    if dept_filter:
        patrons = patrons.filter(department=dept_filter)

    if dept_filter == 'BES':
        # BES Logic: UI 'Year Level' -> DB 'Program', UI 'Program' -> DB 'Major'
        if year_filter:
            patrons = patrons.filter(program=year_filter)
        if program_filter:
            patrons = patrons.filter(major=program_filter)
    else:
        # Standard College Logic
        if program_filter:
            if " - " in program_filter and "Grade" in program_filter:
                prog_part, major_part = program_filter.split(" - ", 1)
                patrons = patrons.filter(program=prog_part, major__icontains=major_part)
            else:
                patrons = patrons.filter(program=program_filter)
        if year_filter:
            patrons = patrons.filter(year_level=year_filter)

    # --- PAGINATION (Fix for Broken Pipe / Slow Loading) ---
    paginator = Paginator(patrons, 50) # Show 50 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preserve filters for pagination links (remove 'page' so it doesn't duplicate)
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    context = {
        'patrons': page_obj,
        'roles': Patron.ROLE_CHOICES,
        'departments': Patron.DEPARTMENT_CHOICES,
        'selected_program': program_filter,
        'selected_year': year_filter,
        'query_params': query_params.urlencode(),
        'current_full_path': request.get_full_path(),
    }
    return render(request, 'library_app/qr_list.html', context)


@login_required
def add_patron(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        id_number = request.POST.get('id_number')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        last_name = request.POST.get('last_name')
        department = request.POST.get('department')
        program = request.POST.get('program')
        major = request.POST.get('major')
        year_level = request.POST.get('year_level')
        email = request.POST.get('email')

        if role == 'guest' and not id_number:
            id_number = f"GUEST-{str(uuid.uuid4())[:8]}"
        elif not id_number:
            messages.error(request, "Error: ID Number is required for Students and Faculty.")
            return redirect('add_patron')

        try:
            patron = Patron.objects.create(
                role=role,
                id_number=id_number,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                department=department,
                program=program,
                major=major,
                year_level=year_level,
                email=email
            )

            if email:
                try:
                    qr_img = qrcode.make(patron.id_number)
                    buffer = BytesIO()
                    qr_img.save(buffer, format="PNG")
                    buffer.seek(0)

                    subject = "UCC Library - Your QR ID"
                    body = f"Hello {patron.first_name},\n\nAttached is your personal QR Code for the library attendance system."

                    email_msg = EmailMessage(
                        subject, body, settings.DEFAULT_FROM_EMAIL, [email],
                    )
                    filename = f"QR_{patron.id_number}.png"
                    email_msg.attach(filename, buffer.getvalue(), 'image/png')
                    email_msg.send(fail_silently=False)
                    messages.success(request, f"User added and QR code sent to {email}!")

                except Exception as email_err:
                    print(f"Email Error: {email_err}")
                    messages.warning(request, "User saved, but email failed to send.")
            else:
                messages.success(request, f"Successfully added {role}: {first_name} {last_name}")

            return redirect('patron_list')

        except Exception as e:
            messages.error(request, f"Error adding user: {e}")

    context = {'department_choices': Patron.DEPARTMENT_CHOICES}
    return render(request, 'library_app/add_patron.html', context)


@login_required
def patron_detail(request, id_number):
    patron = get_object_or_404(Patron, id_number=id_number)
    return render(request, 'library_app/patron_detail.html', {'patron': patron})


@login_required
def update_patron(request, id_number):
    patron = get_object_or_404(Patron, id_number=id_number)
    if request.method == 'POST':
        try:
            # Get the new role first to determine which fields to save
            new_role = request.POST.get('role')

            patron.id_number = request.POST.get('id_number')
            patron.first_name = request.POST.get('first_name')
            patron.middle_name = request.POST.get('middle_name')
            patron.last_name = request.POST.get('last_name')
            patron.role = new_role

            # Conditionally update fields based on role for data integrity
            if new_role == 'student':
                patron.department = request.POST.get('department')
                patron.program = request.POST.get('program')
                patron.major = request.POST.get('major')
                patron.year_level = request.POST.get('year_level')
            elif new_role == 'faculty':
                patron.department = request.POST.get('department')
                patron.program, patron.major, patron.year_level = "", "", ""
            else:  # Guest
                patron.department, patron.program, patron.major, patron.year_level = "", "", "", ""

            # Email Update Logic
            new_email = request.POST.get('email', '').strip()
            patron.email = new_email

            patron.save()
            messages.success(request, "User details updated successfully.")

            # Check for 'HTTP_REFERER' to go back to the previous page
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return HttpResponseRedirect(referer)

            return redirect('patron_list')
        except Exception as e:
            messages.error(request, f"Error updating user: {e}")
            
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return HttpResponseRedirect(referer)

    return redirect('patron_list')


@login_required
def delete_patron(request, id_number):
    patron = get_object_or_404(Patron, id_number=id_number)
    patron.delete()
    messages.success(request, "User deleted successfully.")
    
    # Check for 'HTTP_REFERER' to go back to the previous page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)
        
    return redirect('patron_list')

@login_required
def resend_qr(request, id_number):
    """Manually resend the QR code email to the user."""
    patron = get_object_or_404(Patron, id_number=id_number)
    
    if not patron.email:
        messages.error(request, f"User {patron.first_name} has no email address. Please Edit the user to add one first.")
        # Check for 'HTTP_REFERER' to go back to the previous page
        referer = request.META.get('HTTP_REFERER')
        if referer:
            return HttpResponseRedirect(referer)
        return redirect('patron_list')

    try:
        qr_img = qrcode.make(patron.id_number)
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)

        subject = "UCC Library - Your QR ID (Resent)"
        body = f"Hello {patron.first_name},\n\nHere is a copy of your QR Code for the library attendance system."
        filename = f"QR_{patron.id_number}.png"

        email_msg = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [patron.email])
        email_msg.attach(filename, buffer.getvalue(), 'image/png')
        email_msg.send(fail_silently=False)
        messages.success(request, f"QR Code successfully resent to {patron.email}")
    except Exception as e:
        messages.error(request, f"Failed to send email: {e}")

    # Check for 'HTTP_REFERER' to go back to the previous page
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return HttpResponseRedirect(referer)

    return redirect('patron_list')


# ==========================================
# 3. QR GENERATION & SCANNING
# ==========================================

def generate_qr(request, id_number):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(id_number)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    response = HttpResponse(content_type="image/png")
    img.save(response, "PNG")
    return response


@csrf_exempt
def process_scan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            scanned_id = data.get('qr_code')

            patron = Patron.objects.filter(id_number=scanned_id).first()

            if patron:
                now = timezone.localtime()

                open_session = AttendanceLog.objects.filter(
                    patron=patron,
                    time_out__isnull=True
                ).first()

                if open_session:
                    open_session.time_out = now
                    open_session.save()
                    status_message = "Checked OUT"
                    scan_type = "out"
                else:
                    AttendanceLog.objects.create(patron=patron, scan_time=now)
                    status_message = "Checked IN"
                    scan_type = "in"

                return JsonResponse({
                    'status': 'success',
                    'name': f"{patron.first_name} {patron.last_name}",
                    'id': patron.id_number,
                    'role': patron.role.capitalize(),
                    'time': now.strftime('%I:%M %p'),
                    'type': scan_type,
                    'message': status_message
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'ID not found'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ==========================================
# 4. REPORT GENERATION (PDF)
# ==========================================

def link_callback(uri, rel):
    if settings.STATIC_URL and uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.BASE_DIR, 'library_app', 'static', uri.replace(settings.STATIC_URL, ""))
        if not os.path.isfile(path):
            result = finders.find(uri)
            if result:
                path = result[0] if isinstance(result, (list, tuple)) else result
    elif settings.MEDIA_URL and uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    else:
        return uri

    if not os.path.isfile(path):
        return uri
    return path


def report_selection(request):
    return render(request, 'library_app/report_selection.html')


SCHOOL_DATA = {
    "SBS": [
        "Bachelor of Science in Computer Science",
        "Bachelor of Science in Information Systems",
        "Bachelor of Science in Accountancy",
        "Bachelor of Science in Business Administration",
        "Bachelor of Science in Real Estate Management"
    ],
    "SHES": [
        "Bachelor of Science in Nursing"
    ],
    "SEAS": [
        "Bachelor of Arts in English",
        "Bachelor of Arts in History",
        "Bachelor of Arts in Political Science",
        "Bachelor of Early Childhood Education",
        "Bachelor of Elementary Education",
        "Bachelor of Secondary Education"
    ],
    "GS": [
        "Master of Arts in Education",
        "Master of Arts in Nursing"
    ],
    "BES": [
        "Nursery", "Kinder 1", "Kinder 2",
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
        "Grade 7", "Grade 8", "Grade 9", "Grade 10",
        "Grade 11", "Grade 12"
    ]
}


def print_pdf(request):
    default_year = timezone.now().year
    selected_year = int(request.GET.get('year', default_year))
    selected_sem = request.GET.get('sem', '1')

    if selected_sem == '1':
        months_map = {8: selected_year, 9: selected_year, 10: selected_year, 11: selected_year, 12: selected_year}
        display_name = f"1st Semester, A.Y. {selected_year}-{selected_year + 1}"
        month_names = ["August", "September", "October", "November", "December"]
    else:
        next_year = selected_year + 1
        months_map = {12: selected_year, 1: next_year, 2: next_year, 3: next_year, 4: next_year, 5: next_year}
        display_name = f"2nd Semester, A.Y. {selected_year}-{selected_year + 1}"
        month_names = ["December", "January", "February", "March", "April", "May"]

    report_data = {}

    for dept_code, programs_list in SCHOOL_DATA.items():
        dept_data = {}
        for prog in programs_list:
            monthly_counts = []
            total_prog = 0
            for month_num, year_num in months_map.items():
                count = AttendanceLog.objects.filter(
                    scan_time__month=month_num,
                    scan_time__year=year_num,
                    patron__department=dept_code,
                    patron__program=prog
                ).count()
                monthly_counts.append(count)
                total_prog += count
            monthly_counts.append(total_prog)
            dept_data[prog] = monthly_counts
        report_data[dept_code] = dept_data

    context = {
        'display_name': display_name,
        'month_names': month_names,
        'report_data': report_data,
        'departments': dict(Patron.DEPARTMENT_CHOICES),
    }

    template_path = 'library_app/print_pdf.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Library_Report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return response


# ==========================================
# 5. OTHER UTILS
# ==========================================

@login_required
def manual_checkin(request):
    if request.method == 'POST':
        id_number = request.POST.get('id_number').strip()
        patron = Patron.objects.filter(id_number=id_number).first()

        if not patron:
            messages.error(request, f"ID '{id_number}' not found in the database.")
        else:
            now = timezone.localtime()
            open_session = AttendanceLog.objects.filter(patron=patron, time_out__isnull=True).first()

            if open_session:
                open_session.time_out = now
                open_session.save()
                messages.warning(request, f"CHECKED OUT: {patron.first_name} {patron.last_name}")
            else:
                AttendanceLog.objects.create(patron=patron, scan_time=now)
                messages.success(request, f"CHECKED IN: {patron.first_name} {patron.last_name}")

    return render(request, 'library_app/manual_checkin.html')


@login_required
def scan_history(request):
    date_start = request.GET.get('date_start')
    date_end = request.GET.get('date_end')
    query_id = request.GET.get('q_id')

    logs = AttendanceLog.objects.all().order_by('-scan_time')

    if date_start:
        logs = logs.filter(scan_time__date__gte=date_start)
    if date_end:
        logs = logs.filter(scan_time__date__lte=date_end)
    if query_id:
        logs = logs.filter(patron__id_number__icontains=query_id)

    context = {
        'logs': logs,
        'filter_start': date_start,
        'filter_end': date_end,
        'filter_id': query_id
    }
    return render(request, 'library_app/history.html', context)


@login_required
def bulk_import(request):
    """
    Import students from CSV.
    - Converts Acronyms to Full Names.
    - Converts Year Numbers to Text.
    - DOES NOT send emails.
    """
    if request.method == "POST":
        csv_file = request.FILES.get('csv_file')
        if not csv_file:
            messages.error(request, "Please upload a file.")
            return redirect('bulk_import')
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "File is not a CSV. Please upload a .csv file.")
            return redirect('bulk_import')

        selected_dept = request.POST.get('department')

        ACRONYM_MAP = {
            # SBS
            "BSA": "Bachelor of Science in Accountancy",
            "BSBA": "Bachelor of Science in Business Administration",
            "BSIS": "Bachelor of Science in Information Systems",
            "BSCS": "Bachelor of Science in Computer Science",
            "BSRM": "Bachelor of Science in Real Estate Management",
            "BSREM": "Bachelor of Science in Real Estate Management",

            # SHES
            "BSN": "Bachelor of Science in Nursing",

            # SEAS
            "BA English": "Bachelor of Arts in English",
            "AB English": "Bachelor of Arts in English",
            "BA History": "Bachelor of Arts in History",
            "AB History": "Bachelor of Arts in History",
            "BA PolSci": "Bachelor of Arts in Political Science",
            "AB PolSci": "Bachelor of Arts in Political Science",
            "AB Political Science": "Bachelor of Arts in Political Science",
            "BECEd": "Bachelor of Early Childhood Education",
            "BEEd": "Bachelor of Elementary Education",
            "BSEd": "Bachelor of Secondary Education",
            "BSED": "Bachelor of Secondary Education",
            "BEED": "Bachelor of Elementary Education",
            "BECED": "Bachelor of Early Childhood Education",
            "AB": "Bachelor of Arts",

            # GS
            "MAED": "Master of Arts in Education",
            "MAE": "Master of Arts in Education",
            "MAN": "Master of Arts in Nursing",

            # BES
            "K1": "Kinder 1",
            "K2": "Kinder 2",
            "G1": "Grade 1", "G2": "Grade 2", "G3": "Grade 3",
            "G4": "Grade 4", "G5": "Grade 5", "G6": "Grade 6",
            "G7": "Grade 7", "G8": "Grade 8", "G9": "Grade 9",
            "G10": "Grade 10",
            "1": "Grade 11",
            "2": "Grade 12",
            "SHS": "Grade 11",
        }

        YEAR_MAP = {
            "1": "1st Year",
            "2": "2nd Year",
            "3": "3rd Year",
            "4": "4th Year",
            "11": "Grade 11",
            "12": "Grade 12"
        }

        try:
            decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.DictReader(decoded_file)
            count_created = 0
            count_updated = 0

            for row in reader:
                id_number = row.get('Code', '').strip()
                if not id_number:
                    continue

                first_name = row.get('First Name', '').strip()
                last_name = row.get('Last Name', '').strip()
                middle_name = row.get('Middle Name', '').strip()

                raw_program = row.get('Course', '').strip()
                program = ACRONYM_MAP.get(raw_program, raw_program)
                major = ""

                raw_year = row.get('Year', '').strip()
                year_level = YEAR_MAP.get(raw_year, raw_year)

                # Special Logic for BES Senior High (STEM, ABM, etc.)
                # 1 -> Grade 11, 2 -> Grade 12
                if selected_dept == 'BES' and raw_program.upper() in ["STEM", "ABM", "HUMSS", "GAS", "TVL"]:
                    if raw_year == '1':
                        program = "Grade 11"
                        year_level = "Grade 11"
                    elif raw_year == '2':
                        program = "Grade 12"
                        year_level = "Grade 12"
                    
                    major = f"Academic Track: {raw_program.upper()}"

                raw_email = row.get('Email', '').strip()
                if raw_email and raw_email.lower() != 'nan':
                    email = raw_email.replace(' ', '')
                else:
                    email = None

                patron, created = Patron.objects.update_or_create(
                    id_number=id_number,
                    defaults={
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name,
                        'program': program,
                        'major': major,
                        'year_level': year_level,
                        'email': email,
                        'role': 'student',
                        'department': selected_dept
                    }
                )
                if created:
                    count_created += 1
                else:
                    count_updated += 1

            messages.success(request, f"Import Complete! Created: {count_created}, Updated: {count_updated}.")
            return redirect('patron_list')

        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            return redirect('bulk_import')

    return render(request, 'library_app/bulk_import.html', {
        'departments': Patron.DEPARTMENT_CHOICES
    })


@login_required
def export_patrons_csv(request):
    """Exports all patrons to a CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="patron_list.csv"'

    writer = csv.writer(response)
    # Write the header row
    writer.writerow(['ID Number', 'First Name', 'Middle Name', 'Last Name', 'Email', 'Role', 'Department', 'Program', 'Major', 'Year Level'])

    patrons = Patron.objects.all().order_by('last_name')
    for patron in patrons:
        writer.writerow([
            patron.id_number,
            patron.first_name,
            patron.middle_name,
            patron.last_name,
            patron.email,
            patron.get_role_display(),
            patron.get_department_display(),
            patron.program,
            patron.major,
            patron.year_level
        ])

    return response


# ==========================================
# 6. LOGOUT
# ==========================================

def logout_view(request):
    """Logs the user out and redirects to the login page."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')