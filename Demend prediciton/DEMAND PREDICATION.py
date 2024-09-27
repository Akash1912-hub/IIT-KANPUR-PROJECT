# Import necessary libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import warnings
warnings.filterwarnings('ignore')

# Assuming the uploaded dataset is in CSV format
df = pd.read_csv("/content/yellow_tripdata_2016-01.csv")

# Check the first few rows of the dataset
df.head()

# 1. Feature Engineering

# Convert datetime columns to proper datetime type
df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

# Calculate trip duration in minutes
df['trip_duration'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0

# Create features: hour, day of the week from pickup datetime
df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
df['pickup_day'] = df['tpep_pickup_datetime'].dt.dayofweek

# Filter out unreasonable data points
df = df[(df['trip_distance'] > 0) & (df['trip_duration'] > 0)]

# Fuel consumption estimation
df['estimated_fuel_consumption'] = df['trip_distance'] * 0.15  # Assumed fuel usage factor
df['fare_amount'] = df['trip_distance'] * 2.5 + df['trip_duration'] * 0.5  # Example fare calculation

# 2. Sample the dataset for quicker training
df_sample = df.sample(frac=0.1, random_state=42)  # Sample 10% of the data

# 3. Train models for each prediction task

# Fuel Consumption Prediction
X_fuel = df_sample[['trip_distance', 'trip_duration', 'passenger_count']]
y_fuel = df_sample['estimated_fuel_consumption']
X_fuel_train, X_fuel_test, y_fuel_train, y_fuel_test = train_test_split(X_fuel, y_fuel, test_size=0.3, random_state=42)
rf_fuel_model = RandomForestRegressor(n_estimators=20, random_state=42)
rf_fuel_model.fit(X_fuel_train, y_fuel_train)

# Demand Prediction
demand_per_hour = df_sample.groupby('pickup_hour').size().reset_index(name='demand')
X_demand = demand_per_hour[['pickup_hour']]
y_demand = demand_per_hour['demand']
X_demand_train, X_demand_test, y_demand_train, y_demand_test = train_test_split(X_demand, y_demand, test_size=0.3, random_state=42)
rf_demand_model = RandomForestRegressor(n_estimators=20, random_state=42)
rf_demand_model.fit(X_demand_train, y_demand_train)

# Fare Prediction
fare_features = df_sample[['trip_distance', 'trip_duration', 'passenger_count', 'pickup_longitude', 'pickup_latitude']]
fare_target = df_sample['fare_amount']
X_fare_train, X_fare_test, y_fare_train, y_fare_test = train_test_split(fare_features, fare_target, test_size=0.3, random_state=42)
rf_fare_model = RandomForestRegressor(n_estimators=20, random_state=42)
rf_fare_model.fit(X_fare_train, y_fare_train)

# 4. Define functions for predictions

# Function to predict fuel consumption
def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    input_data = np.array([[trip_distance, trip_duration, passenger_count]])
    prediction = rf_fuel_model.predict(input_data)
    return prediction[0]

# Function to predict demand for a specific hour
def predict_demand(pickup_hour):
    input_data = np.array([[pickup_hour]])
    demand_prediction = rf_demand_model.predict(input_data)
    return demand_prediction[0]

# Function to predict fare based on input parameters
def predict_fare(trip_distance, trip_duration, passenger_count, pickup_longitude, pickup_latitude):
    input_data = np.array([[trip_distance, trip_duration, passenger_count, pickup_longitude, pickup_latitude]])
    fare_prediction = rf_fare_model.predict(input_data)
    return fare_prediction[0]

# Function to get historical demand data for peak hour prediction
def get_peak_hour_data():
    return demand_per_hour.set_index('pickup_hour')['demand'].to_dict()

# Function to get historical demand for a specific pickup hour
def get_peak_hour(pickup_hour, peak_hour_data):
    return peak_hour_data.get(pickup_hour, 0)

# 5. User interaction for predictions

# User input for fuel consumption prediction
print("Enter trip details for fuel consumption prediction:")
trip_distance = float(input("Trip Distance (in miles): "))
trip_duration = float(input("Trip Duration (in minutes): "))
passenger_count = int(input("Passenger Count: "))

fuel_prediction = predict_fuel_consumption(trip_distance, trip_duration, passenger_count)
print(f"Predicted Fuel Consumption: {fuel_prediction:.2f} gallons")

# User input for demand prediction
pickup_hour_demand = int(input("Enter Pickup Hour (0-23) for Demand Prediction: "))
demand_prediction = predict_demand(pickup_hour_demand)
print(f"Predicted Demand at Hour {pickup_hour_demand}: {demand_prediction:.2f} trips")

# User input for fare prediction
print("Enter trip details for fare prediction:")
trip_distance_fare = float(input("Trip Distance (in miles): "))
trip_duration_fare = float(input("Trip Duration (in minutes): "))
passenger_count_fare = int(input("Passenger Count: "))
pickup_longitude = float(input("Pickup Longitude: "))
pickup_latitude = float(input("Pickup Latitude: "))

fare_prediction = predict_fare(trip_distance_fare, trip_duration_fare, passenger_count_fare, pickup_longitude, pickup_latitude)
print(f"Predicted Taxi Fare: ${fare_prediction:.2f}")

# Get peak hour data for historical analysis
peak_hour_data = get_peak_hour_data()

# User input for peak hour prediction
pickup_hour = int(input("Enter Pickup Hour (0-23) for Peak Hour Prediction: "))
peak_hour_demand = get_peak_hour(pickup_hour, peak_hour_data)
print(f"Historical Demand at Hour {pickup_hour}: {peak_hour_demand} trips")
