from waitress import serve
from library_project.wsgi import application
import socket

# Get the local IP address automatically
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)

print(f"Serving on http://{local_ip}:8000")
serve(application, host='0.0.0.0', port=8000)