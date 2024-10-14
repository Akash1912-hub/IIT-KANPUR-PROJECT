'''from flask import Flask, request, jsonify, send_from_directory

import joblib

import requests



# Load the trained model

model = joblib.load('traffic_model.pkl')



# Create Flask app

app = Flask(__name__, static_folder='frontend', static_url_path='')



# Nominatim OpenStreetMap geocoding function

def geocode_location(address):

  try:

    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"

    response = requests.get(url)

    data = response.json()

    if len(data) > 0:

      lat = float(data[0]['lat'])

      lon = float(data[0]['lon'])

      return lat, lon

    else:

      return None, None

  except Exception as e:

    print(f"Error occurred during geocoding: {e}")

    return None, None



# Define route to make predictions

@app.route('/predict', methods=['POST'])

def predict_traffic():

  try:

    data = request.json

    from_place = data.get('from')

    to_place = data.get('to')



    if not from_place or not to_place:

      return jsonify({'error': 'Please provide both starting and destination locations'}), 400



    # Geocode the 'from' and 'to' locations to get latitudes and longitudes

    from_lat, from_lon = geocode_location(from_place)

    to_lat, to_lon = geocode_location(to_place)



    if from_lat is None or to_lat is None:

      return jsonify({'error': 'Geocoding failed for one or both locations'}), 400



    # Prepare the input features for the model

    X_new = [[from_lat, from_lon, to_lat, to_lon]]



    # Make the prediction

    predicted_traffic = model.predict(X_new)



    # Return the prediction as a response

    return jsonify({

      'from': {'latitude': from_lat, 'longitude': from_lon},

      'to': {'latitude': to_lat, 'longitude': to_lon},

      'predicted_traffic_volume': predicted_traffic[0]

    })

  except Exception as e:

    return jsonify({'error': str(e)}), 500



# Serve the frontend

@app.route('/')

def serve_frontend():

  return send_from_directory(app.template_folder, 'index.html')



if __name__ == '__main__':

  app.run(debug=True)'''
from flask import Flask, request, jsonify, send_from_directory
import joblib
import requests
import socket

# Load the trained model
model = joblib.load('traffic_model.pkl')

# Create Flask app
app = Flask(__name__, static_folder='frontend', static_url_path='')

# Nominatim OpenStreetMap geocoding function
def geocode_location(address):
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
        response = requests.get(url)
        data = response.json()
        if len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            return None, None
    except Exception as e:
        print(f"Error occurred during geocoding: {e}")
        return None, None

# Define route to make predictions
@app.route('/predict', methods=['POST'])
def predict_traffic():
    try:
        data = request.json
        from_place = data.get('from')
        to_place = data.get('to')

        if not from_place or not to_place:
            return jsonify({'error': 'Please provide both starting and destination locations'}), 400

        # Geocode the 'from' and 'to' locations to get latitudes and longitudes
        from_lat, from_lon = geocode_location(from_place)
        to_lat, to_lon = geocode_location(to_place)

        if from_lat is None or to_lat is None:
            return jsonify({'error': 'Geocoding failed for one or both locations'}), 400

        # Prepare the input features for the model
        X_new = [[from_lat, from_lon, to_lat, to_lon]]

        # Make the prediction
        predicted_traffic = model.predict(X_new)

        # Return the prediction as a response
        return jsonify({
            'from': {'latitude': from_lat, 'longitude': from_lon},
            'to': {'latitude': to_lat, 'longitude': to_lon},
            'predicted_traffic_volume': predicted_traffic[0]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve the frontend
@app.route('/')
def serve_frontend():
    return send_from_directory(app.template_folder, 'index.html')

# Function to get the local machine's IP address (local IP within the same WiFi)
def get_local_ip():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    return local_ip

# Function to get the global IP address (access from other devices on the same WiFi)
def get_global_ip():
    try:
        # Connect to an external service to retrieve the public IP
        response = requests.get('https://api.ipify.org')
        return response.text
    except Exception as e:
        print(f"Error retrieving global IP: {e}")
        return None

if __name__ == '__main__':
    local_ip = get_local_ip()
    global_ip = get_global_ip()
    
    print(f"Local IP Address (accessible on same device): http://{local_ip}:5000")
    if global_ip:
        print(f"Global IP Address (accessible from other devices on same WiFi): http://{global_ip}:5000")
    else:
        print("Unable to retrieve global IP address.")

    # Run the app on '0.0.0.0' to make it accessible from other devices in the same network
    app.run(host='0.0.0.0', port=5001, debug=True)
