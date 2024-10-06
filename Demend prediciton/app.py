from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib

# Load the models and scalers
fuel_model = joblib.load('fuel_model.pkl')
demand_model = joblib.load('demand_model.pkl')
fare_model = joblib.load('fare_model.pkl')
fuel_scaler = joblib.load('fuel_scaler.pkl')
demand_scaler = joblib.load('demand_scaler.pkl')
fare_scaler = joblib.load('fare_scaler.pkl')

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict_all', methods=['POST'])
def predict_all():
    data = request.json
    
    # Extract inputs
    trip_distance = data['trip_distance']
    trip_duration = data['trip_duration']
    passenger_count = data['passenger_count']
    pickup_hour = data['pickup_hour']
    pickup_longitude = data['pickup_longitude']
    pickup_latitude = data['pickup_latitude']
    
    # Prepare input for fuel model
    fuel_input = pd.DataFrame([[trip_distance, trip_duration, passenger_count]], 
                               columns=['trip_distance', 'trip_duration', 'passenger_count'])
    fuel_input_scaled = fuel_scaler.transform(fuel_input)
    
    # Predict fuel consumption
    fuel_prediction = fuel_model.predict(fuel_input_scaled)[0]
    
    # Prepare input for demand model
    demand_input = pd.DataFrame([[pickup_hour]], columns=['pickup_hour'])
    demand_input_scaled = demand_scaler.transform(demand_input)
    
    # Predict demand
    demand_prediction = demand_model.predict(demand_input_scaled)[0][0]
    
    # Prepare input for fare model
    fare_input = pd.DataFrame([[trip_distance, trip_duration, passenger_count, pickup_longitude, pickup_latitude]], 
                               columns=['trip_distance', 'trip_duration', 'passenger_count', 'pickup_longitude', 'pickup_latitude'])
    fare_input_scaled = fare_scaler.transform(fare_input)
    
    # Predict fare
    fare_prediction = fare_model.predict(fare_input_scaled)[0][0]
    
    # Return all predictions in one response
    return jsonify({
        'predicted_fuel_consumption': float(fuel_prediction),
        'predicted_demand': float(demand_prediction),
        'predicted_fare': float(fare_prediction)
    })

if __name__ == '__main__':
    app.run(debug=True)
