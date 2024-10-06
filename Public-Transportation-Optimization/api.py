from flask import Flask, request, render_template
import joblib
import pandas as pd
import folium
import requests
import polyline

app = Flask(__name__)

# Load the trained model
model = joblib.load('model.pkl')

def preprocess_input(data):
    df = pd.DataFrame([data])

    # Encode categorical features
    categorical_cols = ['DirectionRef', 'PublishedLineName', 'OriginName', 'DestinationName', 'ExpectedArrivalTime', 'ScheduledArrivalTime']
    
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype('category').cat.codes
    
    # Ensure the correct feature order
    expected_order = ['DirectionRef', 'PublishedLineName', 'OriginName', 'OriginLat', 'OriginLong',
                      'DestinationName', 'DestinationLat', 'DestinationLong', 
                      'VehicleLocation.Latitude', 'VehicleLocation.Longitude', 
                      'ExpectedArrivalTime', 'ScheduledArrivalTime', 'hour', 'day']
    
    return df[expected_order]

def generate_map(data):
    origin = [data['OriginLat'], data['OriginLong']]
    vehicle_location = [data['VehicleLocation.Latitude'], data['VehicleLocation.Longitude']]
    destination = [data['DestinationLat'], data['DestinationLong']]

    # Create a Folium map centered around the vehicle's location
    folium_map = folium.Map(location=vehicle_location, zoom_start=12)

    # Add markers for the origin, vehicle location, and destination
    folium.Marker(origin, tooltip="Origin", icon=folium.Icon(color='green')).add_to(folium_map)
    folium.Marker(vehicle_location, tooltip="Vehicle Location", icon=folium.Icon(color='blue')).add_to(folium_map)
    folium.Marker(destination, tooltip="Destination", icon=folium.Icon(color='red')).add_to(folium_map)

    # Get the route from OSRM with the vehicle location as a waypoint
    osrm_url = f'http://router.project-osrm.org/route/v1/driving/{data["OriginLong"]},{data["OriginLat"]};{data["VehicleLocation.Longitude"]},{data["VehicleLocation.Latitude"]};{data["DestinationLong"]},{data["DestinationLat"]}?overview=full'
    
    response = requests.get(osrm_url)
    if response.status_code == 200:
        route_data = response.json()
        route = route_data['routes'][0]['geometry']
        
        # Decode the route into coordinates
        route_coords = polyline.decode(route)

        # Add the route to the map
        folium.PolyLine(locations=route_coords, color='blue', weight=2.5, opacity=1).add_to(folium_map)
    else:
        print(f"Error fetching route: {response.status_code}")

    # Save the map to an HTML file in the static directory
    folium_map.save('static/bus_route_map.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None  # Initialize prediction to None
    if request.method == 'POST':
        # Get the form data with default values to handle missing fields
        data = {
            'DirectionRef': request.form.get('DirectionRef', ''),
            'PublishedLineName': request.form.get('PublishedLineName', ''),
            'OriginName': request.form.get('OriginName', ''),
            'OriginLat': float(request.form.get('OriginLat', 0.0)),
            'OriginLong': float(request.form.get('OriginLong', 0.0)),
            'DestinationName': request.form.get('DestinationName', ''),
            'DestinationLat': float(request.form.get('DestinationLat', 0.0)),
            'DestinationLong': float(request.form.get('DestinationLong', 0.0)),
            'VehicleLocation.Latitude': float(request.form.get('VehicleLocationLat', 0.0)),
            'VehicleLocation.Longitude': float(request.form.get('VehicleLocationLong', 0.0)),
            'ExpectedArrivalTime': request.form.get('ExpectedArrivalTime', ''),
            'ScheduledArrivalTime': request.form.get('ScheduledArrivalTime', ''),
            'hour': int(request.form.get('hour', 0)),
            'day': int(request.form.get('day', 0)),
        }

        # Preprocess the input data
        processed_data = preprocess_input(data)

        # Make a prediction
        prediction = model.predict(processed_data)

        # Generate the map with the given data
        generate_map(data)

        # Render the result page with the prediction and the map
        return render_template('result.html', predicted_distance=prediction[0])

    return render_template('index.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)
