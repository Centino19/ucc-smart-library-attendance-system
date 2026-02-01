@echo off
echo ==========================================
echo      UPDATING LIBRARY SYSTEM
echo ==========================================

echo 1. Pulling latest code from GitHub...
git pull

echo 2. Activating virtual environment...
call .venv\Scripts\activate

echo 3. Installing new libraries (if any)...
pip install -r requirements.txt

echo 4. Updating static files (CSS/JS)...
python manage.py collectstatic --noinput

echo 5. Updating database...
python manage.py migrate

echo.
echo ==========================================
echo      UPDATE COMPLETE!
echo ==========================================
pause