from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- Core ---
    path('', views.landing_page, name='landing_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan/', views.process_scan, name='process_scan'),

    # --- Patron Management ---
    path('patrons/', views.patron_list, name='patron_list'),
    path('add-patron/', views.add_patron, name='add_patron'),
    path('bulk-import/', views.bulk_import, name='bulk_import'),
    path('export-patrons/', views.export_patrons_csv, name='export_patrons_csv'),
    path('patrons/<str:id_number>/', views.patron_detail, name='patron_detail'),
    path('update-patron/<str:id_number>/', views.update_patron, name='update_patron'),
    path('delete-patron/<str:id_number>/', views.delete_patron, name='delete_patron'),
    path('generate-qr/<str:id_number>/', views.generate_qr, name='generate_qr'),
    path('resend-qr/<str:id_number>/', views.resend_qr, name='resend_qr'),

    # --- Attendance & History ---
    path('manual-checkin/', views.manual_checkin, name='manual_checkin'),
    path('history/', views.scan_history, name='scan_history'),

    # --- Reports ---
    path('reports/', views.report_selection, name='report_selection'),
    path('print_pdf/', views.print_pdf, name='print_pdf'),

    # --- Authentication ---
    path('login/', auth_views.LoginView.as_view(template_name='library_app/login.html'), name='login'),

    # FIX IS HERE: Use views.logout_view instead of auth_views.LogoutView
    path('logout/', views.logout_view, name='logout'),
]