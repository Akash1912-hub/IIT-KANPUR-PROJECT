'''from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_socketio import SocketIO
import joblib
import pandas as pd
import gevent
import time
import requests
import socket
from flask_cors import CORS
import logging
from geopy.distance import geodesic

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

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
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to handle trip planning form submission and render result.html
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination = request.form.get('destination')
    passenger_count = request.form.get('passenger_count')

    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination)
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        passenger_count = int(passenger_count)

        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        logging.error(f"An error occurred during trip planning: {e}")
        return f"An error occurred: {e}"

# Route for CO2 prediction page
@app.route('/co2_prediction')
def co2_prediction():
    return render_template('co2_prediction.html')

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Print the host IP address at startup

def print_host_ip():
    host_ip = get_local_ip()
    logging.info(f"Host IP Address: {host_ip}")

# CO2 Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred during CO2 prediction. Please check the input data.'}), 500

# Helper functions for the trip planner

def get_current_location():
    """Returns the fixed current location coordinates for London, UK."""
    return 51.5074, -0.1278  # London coordinates

def get_destination_coordinates(destination_address):
    """Returns the destination coordinates using the Nominatim API based on user input."""
    try:
        encoded_address = requests.utils.quote(destination_address)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json'
        headers = {'User-Agent': 'trip-planner/1.0 (your_email@example.com)'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code: {response.status_code}")
        
        location_data = response.json()
        if location_data:
            result = location_data[0]
            return float(result['lat']), float(result['lon']), result['display_name']
        else:
            raise Exception("No results found for the given address.")
    except Exception as e:
        raise Exception(f"Error in get_destination_coordinates: {e}")

def calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long):
    """Calculates the driving distance and duration between two points using the Google Distance Matrix API."""
    try:
        origins = f"{current_lat},{current_long}"
        destinations = f"{dest_lat},{dest_long}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key={API_KEY}"
        
        response = requests.get(url)
        distance_data = response.json()
        if distance_data['status'] != 'OK':
            raise Exception(f"Distance Matrix API Error: {distance_data['status']}")
        
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Element Status Error: {element['status']}")
        
        distance_text = element['distance']['text']
        duration_text = element['duration']['text']
        
        distance_miles = float(distance_text.replace(' mi', '').replace(',', ''))
        
        # Parse the duration text, which may be in format "X hours Y mins" or "Y mins"
        duration_parts = duration_text.split()
        duration_minutes = 0
        for i in range(0, len(duration_parts), 2):
            time_value = float(duration_parts[i])
            time_unit = duration_parts[i + 1]
            if 'hour' in time_unit:
                duration_minutes += time_value * 60  # Convert hours to minutes
            elif 'min' in time_unit:
                duration_minutes += time_value
        
        return distance_miles, duration_minutes
    except Exception as e:
        logging.error(f"An error occurred while calculating distance and duration: {e}")
        # Fall back to geodesic distance in case of error
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        return distance_miles, estimate_duration(distance_miles)

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=30):
    """Estimates duration based on average speed."""
    return (distance_miles / average_speed) * 60  # Convert hours to minutes

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predict fuel consumption based on distance, duration, and passenger count."""
    fuel_efficiency = 25  # miles per gallon (example)
    consumption = trip_distance / fuel_efficiency
    return consumption

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predict fare based on distance, duration, and passenger count."""
    base_fare = 2.50  # base fare in dollars
    cost_per_mile = 1.00  # cost per mile
    cost_per_minute = 0.20  # cost per minute
    fare = base_fare + (cost_per_mile * trip_distance) + (cost_per_minute * trip_duration)
    return fare

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates a map with the route using Mapbox API."""
    mapbox_url = f'https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-l+FF0000({current_long},{current_lat})/{current_long},{current_lat},{dest_long},{dest_lat}/600x400?access_token={MAPBOX_ACCESS_TOKEN}'
    logging.info(f"Map URL: {mapbox_url}")

# Starting a background thread to fetch Firebase data continuously
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=fetch_data_continuously)

if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 5000 as in the example
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)'''

'''from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_socketio import SocketIO
import joblib
import pandas as pd
import gevent
import time
import requests
import socket
from flask_cors import CORS
import logging
from geopy.distance import geodesic
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Firebase Realtime Database setup
FIREBASE_URL = 'https://ml-transport-1-default-rtdb.firebaseio.com/vehicle_data.json'  # Replace with your Firebase URL
FIREBASE_SECRET = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'  # Replace with your Firebase secret key

# Function to get Firebase data
def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL, params={'auth': FIREBASE_SECRET})
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to handle trip planning form submission and render result.html
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination = request.form.get('destination')
    passenger_count = request.form.get('passenger_count')

    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination)
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        passenger_count = int(passenger_count)

        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        logging.error(f"An error occurred during trip planning: {e}")
        return f"An error occurred: {e}"

# Route for CO2 prediction page
@app.route('/co2_prediction')
def co2_prediction():
    return render_template('co2_prediction.html')

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Print the host IP address at startup
def print_host_ip():
    host_ip = get_local_ip()
    logging.info(f"Host IP Address: {host_ip}")

# CO2 Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred during CO2 prediction. Please check the input data.'}), 500

# Helper functions for the trip planner

def get_current_location():
    """Returns the fixed current location coordinates for London, UK."""
    return 51.5074, -0.1278  # London coordinates

def get_destination_coordinates(destination_address):
    """Returns the destination coordinates using the Nominatim API based on user input."""
    try:
        encoded_address = requests.utils.quote(destination_address)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json'
        headers = {'User-Agent': 'trip-planner/1.0 (your_email@example.com)'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code: {response.status_code}")
        
        location_data = response.json()
        if location_data:
            result = location_data[0]
            return float(result['lat']), float(result['lon']), result['display_name']
        else:
            raise Exception("No results found for the given address.")
    except Exception as e:
        raise Exception(f"Error in get_destination_coordinates: {e}")

def calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long):
    """Calculates the driving distance and duration between two points using the Google Distance Matrix API."""
    try:
        origins = f"{current_lat},{current_long}"
        destinations = f"{dest_lat},{dest_long}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key={API_KEY}"
        
        response = requests.get(url)
        distance_data = response.json()
        if distance_data['status'] != 'OK':
            raise Exception(f"Distance Matrix API Error: {distance_data['status']}")
        
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Element Status Error: {element['status']}")
        
        distance_text = element['distance']['text']
        duration_text = element['duration']['text']
        
        distance_miles = float(distance_text.replace(' mi', '').replace(',', ''))
        
        # Parse the duration text, which may be in format "X hours Y mins" or "Y mins"
        duration_parts = duration_text.split()
        duration_minutes = 0
        for i in range(0, len(duration_parts), 2):
            time_value = float(duration_parts[i])
            time_unit = duration_parts[i + 1]
            if 'hour' in time_unit:
                duration_minutes += time_value * 60  # Convert hours to minutes
            elif 'min' in time_unit:
                duration_minutes += time_value
        
        return distance_miles, duration_minutes
    except Exception as e:
        logging.error(f"An error occurred while calculating distance and duration: {e}")
        # Fall back to geodesic distance in case of error
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        return distance_miles, estimate_duration(distance_miles)

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=30):
    """Estimates duration based on average speed."""
    return (distance_miles / average_speed) * 60  # Convert hours to minutes

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predict fuel consumption based on distance, duration, and passenger count."""
    fuel_efficiency = 25  # miles per gallon (example)
    consumption = trip_distance / fuel_efficiency
    return consumption

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predict fare based on distance, duration, and passenger count."""
    base_fare = 2.50  # base fare in dollars
    cost_per_mile = 1.00  # cost per mile
    cost_per_minute = 0.20  # cost per minute
    fare = base_fare + (cost_per_mile * trip_distance) + (cost_per_minute * trip_duration)
    return fare

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates a map with the route using Mapbox API."""
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
      <title>Map</title>
      <script src="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.js"></script>
      <link href="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.css" rel="stylesheet" />
      <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
      </style>
    </head>
    <body>
      <div id="map"></div>
      <script>
        mapboxgl.accessToken = '{MAPBOX_ACCESS_TOKEN}';
        const map = new mapboxgl.Map({{
          container: 'map',
          style: 'mapbox://styles/mapbox/streets-v11',
          center: [{current_long}, {current_lat}],
          zoom: 10
        }});
        const marker1 = new mapboxgl.Marker({{ color: 'green' }})
          .setLngLat([{current_long}, {current_lat}])
          .setPopup(new mapboxgl.Popup().setHTML('<h3>Current Location: London</h3>'))
          .addTo(map);
        const marker2 = new mapboxgl.Marker({{ color: 'red' }})
          .setLngLat([{dest_long}, {dest_lat}])
          .setPopup(new mapboxgl.Popup().setHTML('<h3>Destination: {destination_address}<br>Distance: {distance:.2f} miles<br>Duration: {duration:.2f} mins<br>Fare: ${fare:.2f}<br>Fuel: {fuel_consumption:.2f} gallons</h3>'))
          .addTo(map);
        const route = [[{current_long}, {current_lat}], [{dest_long}, {dest_lat}]];
        map.on('load', function () {{
          map.addSource('route', {{
            'type': 'geojson',
            'data': {{
              'type': 'Feature',
              'geometry': {{
                'type': 'LineString',
                'coordinates': route
              }}
            }}
          }});
          map.addLayer({{
            'id': 'route',
            'type': 'line',
            'source': 'route',
            'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
            'paint': {{ 'line-color': '#888', 'line-width': 8 }}
          }});
        }});
      </script>
    </body>
    </html>
    """
    # Save the file in the 'static' directory
    map_file_path = os.path.join('static', 'route_map.html')
    with open(map_file_path, 'w') as f:
        f.write(map_html)

# Starting a background thread to fetch Firebase data continuously
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=fetch_data_continuously)

if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 5000 as in the example
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
'''
'''
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
import joblib
import pandas as pd
import requests
import socket
import os
from geopy.distance import geodesic
import logging
import time
from flask_cors import CORS
import gevent

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Google and Mapbox API keys
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Replace with your Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Temporary hard-coded user data for login (replace with a database later)
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
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to handle trip planning form submission and render result.html
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination = request.form.get('destination')
    passenger_count = request.form.get('passenger_count')

    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination)
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        passenger_count = int(passenger_count)

        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        logging.error(f"An error occurred during trip planning: {e}")
        return f"An error occurred: {e}"

# Route for CO2 prediction page
@app.route('/co2_prediction')
def co2_prediction():
    return render_template('co2_prediction.html')

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Print the host IP address at startup
def print_host_ip():
    host_ip = get_local_ip()
    logging.info(f"Host IP Address: {host_ip}")

# CO2 Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred during CO2 prediction. Please check the input data.'}), 500

# Helper functions for trip planning

def get_current_location():
    """Returns the fixed current location coordinates for London, UK."""
    return 51.5074, -0.1278  # London coordinates

def get_destination_coordinates(destination_address):
    """Returns the destination coordinates using the Nominatim API based on user input."""
    try:
        encoded_address = requests.utils.quote(destination_address)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json'
        headers = {'User-Agent': 'trip-planner/1.0 (your_email@example.com)'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code: {response.status_code}")
        
        location_data = response.json()
        if location_data:
            result = location_data[0]
            return float(result['lat']), float(result['lon']), result['display_name']
        else:
            raise Exception("No results found for the given address.")
    except Exception as e:
        raise Exception(f"Error in get_destination_coordinates: {e}")

def calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long):
    """Calculates the driving distance and duration between two points using the Google Distance Matrix API."""
    try:
        origins = f"{current_lat},{current_long}"
        destinations = f"{dest_lat},{dest_long}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key={API_KEY}"
        
        response = requests.get(url)
        distance_data = response.json()
        if distance_data['status'] != 'OK':
            raise Exception(f"Distance Matrix API Error: {distance_data['status']}")
        
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Element Status Error: {element['status']}")
        
        distance_text = element['distance']['text']
        duration_text = element['duration']['text']
        
        distance_miles = float(distance_text.replace(' mi', '').replace(',', ''))
        
        # Parse the duration text, which may be in format "X hours Y mins" or "Y mins"
        duration_parts = duration_text.split()
        duration_minutes = 0
        for i in range(0, len(duration_parts), 2):
            time_value = float(duration_parts[i])
            time_unit = duration_parts[i + 1]
            if 'hour' in time_unit:
                duration_minutes += time_value * 60  # Convert hours to minutes
            elif 'min' in time_unit:
                duration_minutes += time_value
        
        return distance_miles, duration_minutes
    except Exception as e:
        logging.error(f"An error occurred while calculating distance and duration: {e}")
        # Fall back to geodesic distance in case of error
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        return distance_miles, estimate_duration(distance_miles)

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=30):
    """Estimates duration based on average speed."""
    return (distance_miles / average_speed) * 60  # Convert hours to minutes

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predict fuel consumption based on distance, duration, and passenger count."""
    fuel_efficiency = 25  # miles per gallon (example)
    consumption = trip_distance / fuel_efficiency
    return consumption

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predict fare based on distance, duration, and passenger count."""
    base_fare = 2.50  # base fare in dollars
    cost_per_mile = 1.00  # cost per mile
    cost_per_minute = 0.20  # cost per minute
    fare = base_fare + (cost_per_mile * trip_distance) + (cost_per_minute * trip_duration)
    return fare

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates a map with the route using Mapbox API."""
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <title>Map</title>
        <script src="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.js"></script>
        <link href="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.css" rel="stylesheet" />
        <style>body {{ margin: 0; padding: 0; }} #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            mapboxgl.accessToken = '{MAPBOX_ACCESS_TOKEN}';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v11',
                center: [{current_long}, {current_lat}],
                zoom: 10
            }});
            const marker1 = new mapboxgl.Marker({{ color: 'green' }})
                .setLngLat([{current_long}, {current_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Current Location: London</h3>'))
                .addTo(map);
            const marker2 = new mapboxgl.Marker({{ color: 'red' }})
                .setLngLat([{dest_long}, {dest_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Destination: {destination_address}<br>Distance: {distance:.2f} miles<br>Duration: {duration:.2f} mins<br>Fare: ${fare:.2f}<br>Fuel: {fuel_consumption:.2f} gallons</h3>'))
                .addTo(map);
            const route = [[{current_long}, {current_lat}], [{dest_long}, {dest_lat}]];
            map.on('load', function () {{
                map.addSource('route', {{
                    'type': 'geojson',
                    'data': {{
                        'type': 'Feature',
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': route
                        }}
                    }}
                }});
                map.addLayer({{
                    'id': 'route',
                    'type': 'line',
                    'source': 'route',
                    'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                    'paint': {{ 'line-color': '#888', 'line-width': 8 }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    with open(os.path.join('static', 'route_map.html'), 'w') as f:
        f.write(map_html)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Starting a background thread to fetch Firebase data continuously
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=fetch_data_continuously)

if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 8000
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
    '''

'''
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
import joblib
import pandas as pd
import requests
import socket
import os
from geopy.distance import geodesic
import logging
import time
from flask_cors import CORS
import gevent

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Google and Mapbox API keys
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Replace with your Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Temporary hard-coded user data for login (replace with a database later)
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
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to handle trip planning form submission and render result.html
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination = request.form.get('destination')
    passenger_count = request.form.get('passenger_count')

    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination)
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        passenger_count = int(passenger_count)

        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        logging.error(f"An error occurred during trip planning: {e}")
        return f"An error occurred: {e}"

# Route for CO2 prediction page
@app.route('/co2_prediction')
def co2_prediction():
    return render_template('co2_prediction.html')

# Function to optimize route using Google's Directions API (converted from Node.js app.js)
@app.route('/optimize-route', methods=['POST'])
def optimize_route():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')

    if not origin or not destination:
        return jsonify({'error': 'Origin and destination are required.'}), 400

    try:
        response = requests.get(
            'https://maps.googleapis.com/maps/api/directions/json',
            params={
                'origin': origin,
                'destination': destination,
                'key': API_KEY
            }
        )
        response_data = response.json()

        if response.status_code == 200:
            return jsonify(response_data)
        else:
            return jsonify({'error': response_data['status']}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Print the host IP address at startup
def print_host_ip():
    host_ip = get_local_ip()
    logging.info(f"Host IP Address: {host_ip}")

# CO2 Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred during CO2 prediction. Please check the input data.'}), 500

# Helper functions for trip planning

def get_current_location():
    """Returns the fixed current location coordinates for London, UK."""
    return 51.5074, -0.1278  # London coordinates

def get_destination_coordinates(destination_address):
    """Returns the destination coordinates using the Nominatim API based on user input."""
    try:
        encoded_address = requests.utils.quote(destination_address)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json'
        headers = {'User-Agent': 'trip-planner/1.0 (your_email@example.com)'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code: {response.status_code}")
        
        location_data = response.json()
        if location_data:
            result = location_data[0]
            return float(result['lat']), float(result['lon']), result['display_name']
        else:
            raise Exception("No results found for the given address.")
    except Exception as e:
        raise Exception(f"Error in get_destination_coordinates: {e}")

def calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long):
    """Calculates the driving distance and duration between two points using the Google Distance Matrix API."""
    try:
        origins = f"{current_lat},{current_long}"
        destinations = f"{dest_lat},{dest_long}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key={API_KEY}"
        
        response = requests.get(url)
        distance_data = response.json()
        if distance_data['status'] != 'OK':
            raise Exception(f"Distance Matrix API Error: {distance_data['status']}")
        
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Element Status Error: {element['status']}")
        
        distance_text = element['distance']['text']
        duration_text = element['duration']['text']
        
        distance_miles = float(distance_text.replace(' mi', '').replace(',', ''))
        
        # Parse the duration text, which may be in format "X hours Y mins" or "Y mins"
        duration_parts = duration_text.split()
        duration_minutes = 0
        for i in range(0, len(duration_parts), 2):
            time_value = float(duration_parts[i])
            time_unit = duration_parts[i + 1]
            if 'hour' in time_unit:
                duration_minutes += time_value * 60  # Convert hours to minutes
            elif 'min' in time_unit:
                duration_minutes += time_value
        
        return distance_miles, duration_minutes
    except Exception as e:
        logging.error(f"An error occurred while calculating distance and duration: {e}")
        # Fall back to geodesic distance in case of error
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        return distance_miles, estimate_duration(distance_miles)

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=30):
    """Estimates duration based on average speed."""
    return (distance_miles / average_speed) * 60  # Convert hours to minutes

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predict fuel consumption based on distance, duration, and passenger count."""
    fuel_efficiency = 25  # miles per gallon (example)
    consumption = trip_distance / fuel_efficiency
    return consumption

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predict fare based on distance, duration, and passenger count."""
    base_fare = 2.50  # base fare in dollars
    cost_per_mile = 1.00  # cost per mile
    cost_per_minute = 0.20  # cost per minute
    fare = base_fare + (cost_per_mile * trip_distance) + (cost_per_minute * trip_duration)
    return fare

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates a map with the route using Mapbox API."""
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <title>Map</title>
        <script src="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.js"></script>
        <link href="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.css" rel="stylesheet" />
        <style>body {{ margin: 0; padding: 0; }} #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            mapboxgl.accessToken = '{MAPBOX_ACCESS_TOKEN}';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v11',
                center: [{current_long}, {current_lat}],
                zoom: 10
            }});
            const marker1 = new mapboxgl.Marker({{ color: 'green' }})
                .setLngLat([{current_long}, {current_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Current Location: London</h3>'))
                .addTo(map);
            const marker2 = new mapboxgl.Marker({{ color: 'red' }})
                .setLngLat([{dest_long}, {dest_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Destination: {destination_address}<br>Distance: {distance:.2f} miles<br>Duration: {duration:.2f} mins<br>Fare: ${fare:.2f}<br>Fuel: {fuel_consumption:.2f} gallons</h3>'))
                .addTo(map);
            const route = [[{current_long}, {current_lat}], [{dest_long}, {dest_lat}]];
            map.on('load', function () {{
                map.addSource('route', {{
                    'type': 'geojson',
                    'data': {{
                        'type': 'Feature',
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': route
                        }}
                    }}
                }});
                map.addLayer({{
                    'id': 'route',
                    'type': 'line',
                    'source': 'route',
                    'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                    'paint': {{ 'line-color': '#888', 'line-width': 8 }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    with open(os.path.join('static', 'route_map.html'), 'w') as f:
        f.write(map_html)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Starting a background thread to fetch Firebase data continuously
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=fetch_data_continuously)

if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 8000
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
'''
'''
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
import joblib
import pandas as pd
import requests
import socket
import os
from geopy.distance import geodesic
import logging
import time
from flask_cors import CORS
import gevent

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Google and Mapbox API keys
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Replace with your Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Temporary hard-coded user data for login (replace with a database later)
users = {
    "you@example.com": "password123"  # email: password
}

# Firebase Realtime Database setup (if needed)
FIREBASE_URL = 'https://ml-transport-1-default-rtdb.firebaseio.com/vehicle_data.json'  # Replace with your Firebase URL
FIREBASE_SECRET = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'  # Replace with your Firebase secret key

# Function to get Firebase data
def get_firebase_data():
    try:
        response = requests.get(FIREBASE_URL, params={'auth': FIREBASE_SECRET})
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to optimize route using Google Directions API
@app.route('/optimize-route', methods=['POST'])
def optimize_route():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')

    if not origin or not destination:
        return jsonify({'error': 'Origin and destination are required.'}), 400

    try:
        # Call Google Directions API to get the route details
        response = requests.get(
            'https://maps.googleapis.com/maps/api/directions/json',
            params={
                'origin': origin,
                'destination': destination,
                'key': API_KEY
            }
        )
        response_data = response.json()

        if response.status_code == 200:
            return jsonify(response_data)  # Send the route data to the frontend
        else:
            return jsonify({'error': response_data['status']}), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Other helper functions...

if __name__ == "__main__":
    ip_address = socket.gethostbyname(socket.gethostname())  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 8000

    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
'''
from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
import joblib
import pandas as pd
import requests
import socket
import os
from geopy.distance import geodesic
import logging
import time
from flask_cors import CORS
import gevent

# Set up logging
logging.basicConfig(level=logging.INFO)

# Flask app initialization
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='gevent')  # Using gevent as async mode

# Google and Mapbox API keys
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Replace with your Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Temporary hard-coded user data for login (replace with a database later)
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
        logging.error(f"Error retrieving data from Firebase: {e}")
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

# Route for demand prediction form (intex.html)
@app.route('/intex.html')
def demand_page():
    return render_template('intex.html')

# Route to handle trip planning form submission and render result.html
@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination = request.form.get('destination')
    passenger_count = request.form.get('passenger_count')

    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination)
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        passenger_count = int(passenger_count)

        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        logging.error(f"An error occurred during trip planning: {e}")
        return f"An error occurred: {e}"

# Route for CO2 prediction page
@app.route('/co2_prediction')
def co2_prediction():
    return render_template('co2_prediction.html')

# Function to get the local machine's IP address
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Print the host IP address at startup
def print_host_ip():
    host_ip = get_local_ip()
    logging.info(f"Host IP Address: {host_ip}")

# CO2 Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({'error': 'An error occurred during CO2 prediction. Please check the input data.'}), 500

# Helper functions for trip planning

def get_current_location():
    """Returns the fixed current location coordinates for London, UK."""
    return 51.5074, -0.1278  # London coordinates

def get_destination_coordinates(destination_address):
    """Returns the destination coordinates using the Nominatim API based on user input."""
    try:
        encoded_address = requests.utils.quote(destination_address)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json'
        headers = {'User-Agent': 'trip-planner/1.0 (your_email@example.com)'}
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Request failed with status code: {response.status_code}")
        
        location_data = response.json()
        if location_data:
            result = location_data[0]
            return float(result['lat']), float(result['lon']), result['display_name']
        else:
            raise Exception("No results found for the given address.")
    except Exception as e:
        raise Exception(f"Error in get_destination_coordinates: {e}")

def calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long):
    """Calculates the driving distance and duration between two points using the Google Distance Matrix API."""
    try:
        origins = f"{current_lat},{current_long}"
        destinations = f"{dest_lat},{dest_long}"
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins={origins}&destinations={destinations}&key={API_KEY}"
        
        response = requests.get(url)
        distance_data = response.json()
        if distance_data['status'] != 'OK':
            raise Exception(f"Distance Matrix API Error: {distance_data['status']}")
        
        element = distance_data['rows'][0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Element Status Error: {element['status']}")
        
        distance_text = element['distance']['text']
        duration_text = element['duration']['text']
        
        distance_miles = float(distance_text.replace(' mi', '').replace(',', ''))
        
        # Parse the duration text, which may be in format "X hours Y mins" or "Y mins"
        duration_parts = duration_text.split()
        duration_minutes = 0
        for i in range(0, len(duration_parts), 2):
            time_value = float(duration_parts[i])
            time_unit = duration_parts[i + 1]
            if 'hour' in time_unit:
                duration_minutes += time_value * 60  # Convert hours to minutes
            elif 'min' in time_unit:
                duration_minutes += time_value
        
        return distance_miles, duration_minutes
    except Exception as e:
        logging.error(f"An error occurred while calculating distance and duration: {e}")
        # Fall back to geodesic distance in case of error
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        return distance_miles, estimate_duration(distance_miles)

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=30):
    """Estimates duration based on average speed."""
    return (distance_miles / average_speed) * 60  # Convert hours to minutes

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predict fuel consumption based on distance, duration, and passenger count."""
    fuel_efficiency = 25  # miles per gallon (example)
    consumption = trip_distance / fuel_efficiency
    return consumption

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predict fare based on distance, duration, and passenger count."""
    base_fare = 2.50  # base fare in dollars
    cost_per_mile = 1.00  # cost per mile
    cost_per_minute = 0.20  # cost per minute
    fare = base_fare + (cost_per_mile * trip_distance) + (cost_per_minute * trip_duration)
    return fare

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates a map with the route using Mapbox API."""
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
        <title>Map</title>
        <script src="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.js"></script>
        <link href="https://api.mapbox.com/mapbox-gl-js/v2.11.0/mapbox-gl.css" rel="stylesheet" />
        <style>body {{ margin: 0; padding: 0; }} #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}</style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            mapboxgl.accessToken = '{MAPBOX_ACCESS_TOKEN}';
            const map = new mapboxgl.Map({{
                container: 'map',
                style: 'mapbox://styles/mapbox/streets-v11',
                center: [{current_long}, {current_lat}],
                zoom: 10
            }});
            const marker1 = new mapboxgl.Marker({{ color: 'green' }})
                .setLngLat([{current_long}, {current_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Current Location: London</h3>'))
                .addTo(map);
            const marker2 = new mapboxgl.Marker({{ color: 'red' }})
                .setLngLat([{dest_long}, {dest_lat}])
                .setPopup(new mapboxgl.Popup().setHTML('<h3>Destination: {destination_address}<br>Distance: {distance:.2f} miles<br>Duration: {duration:.2f} mins<br>Fare: ${fare:.2f}<br>Fuel: {fuel_consumption:.2f} gallons</h3>'))
                .addTo(map);
            const route = [[{current_long}, {current_lat}], [{dest_long}, {dest_lat}]];
            map.on('load', function () {{
                map.addSource('route', {{
                    'type': 'geojson',
                    'data': {{
                        'type': 'Feature',
                        'geometry': {{
                            'type': 'LineString',
                            'coordinates': route
                        }}
                    }}
                }});
                map.addLayer({{
                    'id': 'route',
                    'type': 'line',
                    'source': 'route',
                    'layout': {{ 'line-join': 'round', 'line-cap': 'round' }},
                    'paint': {{ 'line-color': '#888', 'line-width': 8 }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    with open(os.path.join('static', 'route_map.html'), 'w') as f:
        f.write(map_html)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Starting a background thread to fetch Firebase data continuously
@socketio.on('connect')
def handle_connect():
    socketio.start_background_task(target=fetch_data_continuously)

if __name__ == "__main__":
    ip_address = get_local_ip()  # Get the machine's IP address
    print(f"Server is running at http://{ip_address}:8000")  # Use port 8000
    
    gevent.spawn(fetch_data_continuously)  # Start background thread to fetch data
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)