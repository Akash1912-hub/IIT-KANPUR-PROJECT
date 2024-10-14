'''from flask import Flask, render_template
from flask_socketio import SocketIO
import gevent
import time
import requests
import socket

# Flask app initialization
app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Firebase Realtime Database setup
FIREBASE_URL = 'https://ml-transport-1-default-rtdb.firebaseio.com/vehicle_data.json'  # Replace with your Firebase URL
FIREBASE_SECRET = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'  # Replace with your Firebase secret key

# Function to get Firebase data
def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL, params={'auth': FIREBASE_SECRET})
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data from Firebase: {e}")
        return {}

# Function to continuously fetch data from Firebase and send updates to frontend
def fetch_data_continuously():
    while True:
        firebase_data = get_firebase_data()
        socketio.emit('firebase_update', firebase_data)  # Emit the data to frontend using WebSocket
        time.sleep(5)  # Fetch data every 5 seconds

# Route for the home page
@app.route('/')
def home():
    return render_template('firebase_data_socketio.html')  # Renders the HTML page

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Main section to run the application
if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)  # Run Flask app on all network interfaces
'''
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import gevent
import time
import requests
import socket

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Temporary hard-coded user data for login (you can replace this with a database later)
users = {
    "you@example.com": "password123"  # email: password
}

# Firebase Realtime Database setup
FIREBASE_URL = 'https://ml-transport-1-default-rtdb.firebaseio.com/vehicle_data.json'  # Replace with your Firebase URL
FIREBASE_SECRET = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'  # Replace with your Firebase secret key

# Function to get Firebase data
def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL, params={'auth': FIREBASE_SECRET})
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving data from Firebase: {e}")
        return {}

# Function to continuously fetch data from Firebase and send updates to frontend
def fetch_data_continuously():
    while True:
        firebase_data = get_firebase_data()
        socketio.emit('firebase_update', firebase_data)  # Emit the data to frontend using WebSocket
        time.sleep(5)  # Fetch data every 5 seconds

# Route for login page
@app.route('/')
def login_page():
    return render_template('login.html')

# Route to handle login form submission
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Check if the user exists and the password matches
    if email in users and users[email] == password:
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid email or password."}), 401

# Route for dashboard (after successful login)
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Main section to run the application
if __name__ == "__main__":
    # Start the background thread to fetch data from Firebase
    gevent.spawn(fetch_data_continuously)
    
    # Run Flask app on all network interfaces
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)  
