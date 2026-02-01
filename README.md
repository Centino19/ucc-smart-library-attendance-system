# 📚 UCC Library Attendance System

A smart, QR code-based attendance monitoring system designed for the University of Camarin (UCC) Library. This system streamlines student login/logout, tracks library usage, and generates detailed PDF reports.

## 🚀 Key Features

### 🔹 Core Functionality
*   **QR Code Scanning:** Fast check-in and check-out using a webcam or mobile device.
*   **Real-Time Dashboard:** Live statistics, charts (Chart.js), and "Top 5" leaderboards.
*   **Auto-Checkout:** Automatically closes open sessions at 5:00 PM daily to ensure data accuracy.
*   **Manual Entry:** Fallback option for students who forgot their IDs.
*   **Offline Mode:** Scanner works without internet access (using local assets).

### 🔹 User Management
*   **Patron Database:** Supports College Students, Basic Education (K-12), Faculty, and Guests.
*   **Bulk Import:** Upload users via CSV with intelligent acronym mapping (e.g., "BSCS" -> "Bachelor of Science in Computer Science").
*   **QR Generation:** Automatically generates and emails QR codes to users upon registration.

### 🔹 Reporting & Analytics
*   **PDF Reports:** Generate professional attendance reports by Semester or Month.
*   **Scan History:** Searchable logs with date filtering.
*   **Data Export:** Export user lists to CSV.
*   **System Audit Logs:** Track admin actions (Add, Edit, Delete, Print) for security.

## 🛠️ Tech Stack
*   **Backend:** Django 6.0, Python 3.11+
*   **Frontend:** Bootstrap 5, JavaScript, Chart.js
*   **Database:** PostgreSQL (Production) / SQLite (Dev)
*   **PDF Engine:** xhtml2pdf
*   **Scanner:** html5-qrcode
*   **Server:** Waitress (Production WSGI)

## ⚙️ Installation Guide

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Centino19/ucc-smart-library-attendance-system.git
    cd ucc-smart-library-attendance-system
    ```

2.  **Create Virtual Environment:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root folder and add your secrets:
    ```ini
    SECRET_KEY=your_django_secret_key
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_app_password
    # Optional DB Config (Defaults to local postgres/1234 if missing)
    DB_NAME=library_db
    DB_USER=postgres
    DB_PASSWORD=your_db_password
    ```

5.  **Setup Database:**
    ```bash
    python manage.py migrate
    ```

6.  **Create Admin User:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the System:**
    ```bash
    # For Production (Recommended)
    python run_production.py
    
    # For Development
    python manage.py runserver
    ```

## 📱 Mobile Scanner Setup (Ngrok)
To use a mobile phone as a scanner:
1.  Install **Ngrok**.
2.  Run `ngrok http 8000` in a terminal.
3.  Use the `https` link provided by Ngrok on your mobile device.
4.  The camera will work instantly (bypassing browser security restrictions on HTTP).

## ⏰ Automatic Checkout
The system includes a management command to force-checkout users who forgot to log out.
*   **Automatic:** Runs daily at 5:00 PM (via APScheduler).
*   **Manual:** Run `python manage.py force_checkout` in the terminal.