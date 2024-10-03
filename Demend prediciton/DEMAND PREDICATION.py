import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor as RF_Sklearn
from sklearn.preprocessing import StandardScaler as SS_Sklearn
import tensorflow as tf
import warnings
warnings.filterwarnings('ignore')

try:
    from daal4py.sklearn.ensemble import RandomForestRegressor as RF_Intel
    from daal4py.sklearn.preprocessing import StandardScaler as SS_Intel
    use_onedal = True
    print("Using Intel oneDAL")
except ImportError:
    use_onedal = False
    print("Intel oneDAL not available. Using scikit-learn instead.")


#print("TensorFlow version:", tf.__version__)

try:
    build_info = tf.sysconfig.get_build_info()
    print("Built with oneDNN:", 'mkl' in build_info.get('build_config', ''))
except AttributeError:
    print("MKL check not supported in this TensorFlow version.")


tf.config.optimizer.set_jit(True)

df = pd.read_csv("/content/yellow_tripdata_2015-01.csv")

df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
df['trip_duration'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0
df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
df['pickup_day'] = df['tpep_pickup_datetime'].dt.dayofweek
df = df[(df['trip_distance'] > 0) & (df['trip_duration'] > 0)]
df['estimated_fuel_consumption'] = df['trip_distance'] * 0.15
df['fare_amount'] = df['trip_distance'] * 2.5 + df['trip_duration'] * 0.5

df_sample = df.sample(frac=0.1, random_state=42)


def train_rf_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    if use_onedal:
        scaler = SS_Intel()
        model = RF_Intel(n_estimators=20, random_state=42)
    else:
        scaler = SS_Sklearn()
        model = RF_Sklearn(n_estimators=20, random_state=42)
    
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    mse = np.mean((y_test - y_pred) ** 2)
    print(f"Mean Squared Error: {mse}")
    
    return model, scaler

def train_tf_model(X, y, epochs=50, batch_size=32):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    if use_onedal:
        scaler = SS_Intel()
    else:
        scaler = SS_Sklearn()
    
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    history = model.fit(X_train_scaled, y_train, 
                        epochs=epochs, 
                        batch_size=batch_size,
                        validation_split=0.2,
                        verbose=0)
    
    test_loss, test_mae = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"Test Mean Absolute Error: {test_mae}")
    
    return model, scaler

print("Training Fuel Consumption Model (Random Forest):")
X_fuel = df_sample[['trip_distance', 'trip_duration', 'passenger_count']]
y_fuel = df_sample['estimated_fuel_consumption']
fuel_model, fuel_scaler = train_rf_model(X_fuel, y_fuel)

print("\nTraining Demand Model (TensorFlow with oneDNN):")
demand_per_hour = df_sample.groupby('pickup_hour').size().reset_index(name='demand')
X_demand = demand_per_hour[['pickup_hour']]
y_demand = demand_per_hour['demand']
demand_model, demand_scaler = train_tf_model(X_demand, y_demand)

print("\nTraining Fare Model (TensorFlow with oneDNN):")
fare_features = df_sample[['trip_distance', 'trip_duration', 'passenger_count', 'pickup_longitude', 'pickup_latitude']]
fare_target = df_sample['fare_amount']
fare_model, fare_scaler = train_tf_model(fare_features, fare_target)

def predict_fuel_consumption(trip_distance, trip_duration, passenger_count):
    input_data = np.array([[trip_distance, trip_duration, passenger_count]])
    input_data_scaled = fuel_scaler.transform(input_data)
    prediction = fuel_model.predict(input_data_scaled)
    return prediction[0]

def predict_demand(pickup_hour):
    input_data = np.array([[pickup_hour]])
    input_data_scaled = demand_scaler.transform(input_data)
    demand_prediction = demand_model.predict(input_data_scaled)
    return demand_prediction[0][0]

def predict_fare(trip_distance, trip_duration, passenger_count, pickup_longitude, pickup_latitude):
    input_data = np.array([[trip_distance, trip_duration, passenger_count, pickup_longitude, pickup_latitude]])
    input_data_scaled = fare_scaler.transform(input_data)
    fare_prediction = fare_model.predict(input_data_scaled)
    return fare_prediction[0][0]

def get_peak_hour_data():
    return demand_per_hour.set_index('pickup_hour')['demand'].to_dict()

def get_peak_hour(pickup_hour, peak_hour_data):
    return peak_hour_data.get(pickup_hour, 0)

print("\nEnter trip details for fuel consumption prediction:")
trip_distance = float(input("Trip Distance (in miles): "))
trip_duration = float(input("Trip Duration (in minutes): "))
passenger_count = int(input("Passenger Count: "))

fuel_prediction = predict_fuel_consumption(trip_distance, trip_duration, passenger_count)
print(f"Predicted Fuel Consumption: {fuel_prediction:.2f} gallons")

pickup_hour_demand = int(input("\nEnter Pickup Hour (0-23) for Demand Prediction: "))
demand_prediction = predict_demand(pickup_hour_demand)
print(f"Predicted Demand at Hour {pickup_hour_demand}: {demand_prediction:.2f} trips")

print("\nEnter trip details for fare prediction:")
trip_distance_fare = float(input("Trip Distance (in miles): "))
trip_duration_fare = float(input("Trip Duration (in minutes): "))
passenger_count_fare = int(input("Passenger Count: "))
pickup_longitude = float(input("Pickup Longitude: "))
pickup_latitude = float(input("Pickup Latitude: "))

fare_prediction = predict_fare(trip_distance_fare, trip_duration_fare, passenger_count_fare, pickup_longitude, pickup_latitude)
print(f"Predicted Taxi Fare: ${fare_prediction:.2f}")

peak_hour_data = get_peak_hour_data()
pickup_hour = int(input("\nEnter Pickup Hour (0-23) for Peak Hour Prediction: "))
peak_hour_demand = get_peak_hour(pickup_hour, peak_hour_data)
print(f"Historical Demand at Hour {pickup_hour}: {peak_hour_demand} trips")
