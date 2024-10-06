import pandas as pd
import numpy as np
import joblib  # Import joblib to save the models
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor as RF_Sklearn
from sklearn.preprocessing import StandardScaler as SS_Sklearn
import tensorflow as tf
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Load the data from a CSV file
df = pd.read_csv(r"C:\Users\HP\Desktop\yellow_tripdata_2015-01.csv")

# Convert datetime columns with error handling
df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'], errors='coerce')
df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'], errors='coerce')

# Calculate trip duration and other derived features
df['trip_duration'] = (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime']).dt.total_seconds() / 60.0
df['pickup_hour'] = df['tpep_pickup_datetime'].dt.hour
df['pickup_day'] = df['tpep_pickup_datetime'].dt.dayofweek

# Filter out invalid trips
df = df[(df['trip_distance'] > 0) & (df['trip_duration'] > 0)]
df['estimated_fuel_consumption'] = df['trip_distance'] * 0.15
df['fare_amount'] = df['trip_distance'] * 2.5 + df['trip_duration'] * 0.5

# Sample the data for training
df_sample = df.sample(frac=0.1, random_state=42)

def train_rf_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
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
    # Check for NaN values in features and target
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        raise ValueError("Input data contains NaN values.")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    scaler = SS_Sklearn()
    
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Print shapes for debugging
    print("X_train_scaled shape:", X_train_scaled.shape)
    print("y_train shape:", y_train.shape)

    # Check for NaN values in scaled features and target
    if np.any(np.isnan(X_train_scaled)) or np.any(np.isnan(y_train)):
        raise ValueError("Scaled input data or target contains NaN values.")
    
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    # Fit the model
    try:
        history = model.fit(X_train_scaled, y_train, 
                            epochs=epochs, 
                            batch_size=batch_size,
                            validation_split=0.2,
                            verbose=1)  # Set verbose to 1 to get detailed output
    except Exception as e:
        print(f"Error during model fitting: {e}")
        return None, None

    test_loss, test_mae = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"Test Mean Absolute Error: {test_mae}")
    
    return model, scaler

# Train models
print("Training Fuel Consumption Model (Random Forest):")
X_fuel = df_sample[['trip_distance', 'trip_duration', 'passenger_count']]
y_fuel = df_sample['estimated_fuel_consumption']
fuel_model, fuel_scaler = train_rf_model(X_fuel, y_fuel)

print("\nTraining Demand Model (TensorFlow):")
demand_per_hour = df_sample.groupby('pickup_hour').size().reset_index(name='demand')
X_demand = demand_per_hour[['pickup_hour']]
y_demand = demand_per_hour['demand']
demand_model, demand_scaler = train_tf_model(X_demand, y_demand)

print("\nTraining Fare Model (TensorFlow):")
fare_features = df_sample[['trip_distance', 'trip_duration', 'passenger_count', 'pickup_longitude', 'pickup_latitude']]
fare_target = df_sample['fare_amount']
fare_model, fare_scaler = train_tf_model(fare_features, fare_target)

# Save the DataFrame, models, and scalers
df.to_pickle("yellow_tripdata_2015-01.pkl")  # Save DataFrame as .pkl
joblib.dump(fuel_model, 'fuel_model.pkl')     # Save Random Forest model
joblib.dump(demand_model, 'demand_model.pkl') # Save TensorFlow model
joblib.dump(fare_model, 'fare_model.pkl')     # Save Fare model
joblib.dump(fuel_scaler, 'fuel_scaler.pkl')   # Save Fuel Scaler
joblib.dump(demand_scaler, 'demand_scaler.pkl') # Save Demand Scaler
joblib.dump(fare_scaler, 'fare_scaler.pkl')   # Save Fare Scaler

print("DataFrame and models have been saved as .pkl files.")
