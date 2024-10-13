from flask import Flask, request, render_template
import requests
from geopy.distance import geodesic
import os

app = Flask(__name__)

# ------------------------------ Configuration ------------------------------
API_KEY = 'AIzaSyC-YzP5XfZL2GHBhtyl4TgsHblzT25ttSo'  # Replace with your actual Google API key
MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiZ29rdWxha3Jpc2huYW4tNjEwIiwiYSI6ImNtMjdkNWxpaDFiZWoyaXM2czRhZTY0cGoifQ.hv7LUuaUken_pJ88fsvYKA'  # Replace with your Mapbox access token

# Create the static directory if it doesn't exist
if not os.path.exists('static'):
    os.makedirs('static')

# ------------------------------ Functions ------------------------------

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
        duration_minutes = sum(float(duration_parts[i]) * (60 if 'hour' in duration_parts[i + 1] else 1) 
                               for i in range(0, len(duration_parts), 2) for duration_parts in duration_text.split())
        
        return distance_miles, duration_minutes
    except Exception as e:
        print(f"An error occurred while calculating distance and duration: {e}")
        distance_miles = calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long)
        duration_minutes = estimate_duration(distance_miles)
        print("Using geodesic distance and estimated duration instead.")
        return distance_miles, duration_minutes

def calculate_geodesic_distance(current_lat, current_long, dest_lat, dest_long):
    """Calculates the great-circle distance between two points using geopy."""
    return geodesic((current_lat, current_long), (dest_lat, dest_long)).miles

def estimate_duration(distance_miles, average_speed=60):
    """Estimates travel duration based on distance and average speed."""
    return (distance_miles / average_speed) * 60

def generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption):
    """Generates an interactive map with markers for the current location and destination."""
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
    with open('static/route_map.html', 'w') as f:
        f.write(map_html)

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    """Predicts fuel consumption based on trip distance, duration, and passenger count."""
    return (trip_distance * 0.05) + (trip_duration * 0.01) + (passenger_count * 0.1)

def predict_fare(trip_distance, trip_duration, passenger_count):
    """Predicts fare based on trip distance, duration, and passenger count."""
    return (trip_distance * 2) + (trip_duration * 0.5) + (passenger_count * 1.5)

# ------------------------------ Routes ------------------------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/plan_trip', methods=['POST'])
def plan_trip():
    destination_input = request.form['destination']
    passenger_count_input = request.form['passenger_count']
    
    current_lat, current_long = get_current_location()
    
    try:
        dest_lat, dest_long, destination_address = get_destination_coordinates(destination_input)
        
        distance, duration = calculate_distance_and_duration(current_lat, current_long, dest_lat, dest_long)
        
        passenger_count = int(passenger_count_input)
        fuel_consumption = predict_fuel_consumption(distance, duration, passenger_count)
        fare = predict_fare(distance, duration, passenger_count)

        generate_map(current_lat, current_long, dest_lat, dest_long, destination_address, distance, duration, fare, fuel_consumption)

        return render_template('result.html', destination=destination_address,
                               distance=distance, duration=duration,
                               fare=fare, fuel_consumption=fuel_consumption)

    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    app.run(port=5001, debug=True)
