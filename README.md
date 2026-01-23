# Library Attendance System

A comprehensive web-based application designed to streamline library attendance tracking using QR code technology. Built with Django, this system allows for real-time monitoring of library usage, automated reporting, and efficient patron management.

## 🚀 Features

### 🔹 Core Functionality
*   **QR Code Scanning:** Fast check-in and check-out using a webcam or barcode scanner.
*   **Real-Time Dashboard:** Live statistics on daily visits, current occupancy, and historical trends using interactive charts (Chart.js).
*   **Manual Entry:** Fallback option to manually input ID numbers if scanning fails.

### 🔹 User Management
*   **User Database:** Manage student and faculty records (Add, Edit, Delete).
*   **Bulk Import:** Upload students via CSV to populate the database quickly.
*   **QR Generation:** Automatically generates unique QR codes for every user.
*   **Email Integration:** Sends the generated QR code directly to the user's registered email immediately after creation.

### 🔹 Reporting & Analytics
*   **PDF Reports:** Generate detailed attendance reports for specific semesters or months ready for printing.
*   **Scan History:** View and filter logs by date range or specific user ID.
*   **Leaderboards:** Tracks "Top 5 Visitors" and "Top Study Leaders" (time spent inside).

## 🛠️ Tech Stack

*   **Backend:** Python, Django 6.0
*   **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript
*   **Charts:** Chart.js
*   **Database:** SQLite (Default)
*   **PDF Generation:** xhtml2pdf
*   **QR Processing:** qrcode, Pillow

## ⚙️ Installation Guide

Follow these steps to set up the project locally.

### Prerequisites
*   Python 3.10+ installed.

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/library-attendance-system.git
cd library-attendance-system
```

### 2. Create a Virtual Environment
**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```
**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
Initialize the local database:
```bash
python manage.py migrate
```

### 5. Create Admin User
Create a superuser to access the dashboard:
```bash
python manage.py createsuperuser
```

### 6. Email Configuration (Optional)
To enable the feature that emails QR codes to users:
1.  Open `library_project/settings.py`.
2.  Locate the `EMAIL CONFIGURATION` section at the bottom.
3.  Update `EMAIL_HOST_USER` with your Gmail address.
4.  Update `EMAIL_HOST_PASSWORD` with your **Gmail App Password** (not your login password).

### 7. Run the Server
```bash
python manage.py runserver
```
Access the application at: `http://127.0.0.1:8000/`

## 📸 Usage

1.  **Login:** Use your superuser credentials to log in.
2.  **Dashboard:** View stats. The page auto-refreshes every 10 seconds to keep data current.
3.  **Scanner Mode:** Navigate to "Scanner Mode" to start processing students.
4.  **Register Users:** Go to "Register User" to add single users or "Bulk Import" for CSV uploads.
