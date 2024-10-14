import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras import layers, models

# Load the dataset
df = pd.read_csv('traffic_data_with_timing.csv')
print(df.head())

# Define features and target
X = df[['time_of_day', 'day_of_week', 'vehicle_count_north', 'vehicle_count_south', 'vehicle_count_east', 'vehicle_count_west']]
y = df['optimum_timing']

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Define and compile the model
model = models.Sequential([
    layers.Input(shape=(X_train_scaled.shape[1],)), 
    layers.Dense(64, activation='relu'),            
    layers.Dense(32, activation='relu'),            
    layers.Dense(1)                                 
])

model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])

# Train the model
history = model.fit(X_train_scaled, y_train, epochs=100, batch_size=4, validation_split=0.2, verbose=1)

# Evaluate the model
test_loss, test_mae = model.evaluate(X_test_scaled, y_test, verbose=1)
print(f"Test Mean Absolute Error: {test_mae}")

# Make predictions
predictions = model.predict(X_test_scaled)
num_predictions = min(len(predictions), len(y_test))

for i in range(num_predictions):
    print(f"Predicted: {predictions[i][0]}, Actual: {y_test.iloc[i]}")

# Save the model
model.save('traffic_optimum_timing_model.h5')
print("Model saved as 'traffic_optimum_timing_model.h5'")
