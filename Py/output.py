import tensorflow as tf
import pandas as pd
from sklearn.preprocessing import StandardScaler

# Load the saved models for each direction
model_north = tf.keras.models.load_model('traffic_signal_model_north.h5')
model_south = tf.keras.models.load_model('traffic_signal_model_south.h5')
model_east = tf.keras.models.load_model('traffic_signal_model_east.h5')
model_west = tf.keras.models.load_model('traffic_signal_model_west.h5')

# Load the dataset to fit the scaler
df = pd.read_csv('traffic_signal_data_directions.csv')
X = df[['time_of_day', 'day_of_week', 'vehicle_count_north', 'vehicle_count_south', 'vehicle_count_east', 'vehicle_count_west']]

# Fit the scaler
scaler = StandardScaler()
scaler.fit(X)

def get_user_input():
    # Collect user input for vehicle counts and time
    time_of_day = float(input("Enter time of day (0-23): "))
    day_of_week = int(input("Enter day of week (1-7): "))
    vehicle_count_north = float(input("Enter vehicle count (north): "))
    vehicle_count_south = float(input("Enter vehicle count (south): "))
    vehicle_count_east = float(input("Enter vehicle count (east): "))
    vehicle_count_west = float(input("Enter vehicle count (west): "))

    # Create a DataFrame from the input data
    user_data = pd.DataFrame({
        'time_of_day': [time_of_day],
        'day_of_week': [day_of_week],
        'vehicle_count_north': [vehicle_count_north],
        'vehicle_count_south': [vehicle_count_south],
        'vehicle_count_east': [vehicle_count_east],
        'vehicle_count_west': [vehicle_count_west]
    })

    return user_data

def predict_signal_times(user_data):
    # Normalize user data
    user_data_scaled = scaler.transform(user_data)

    # Predict green light time for each direction
    green_north = model_north.predict(user_data_scaled)[0][0]
    green_south = model_south.predict(user_data_scaled)[0][0]
    green_east = model_east.predict(user_data_scaled)[0][0]
    green_west = model_west.predict(user_data_scaled)[0][0]

    # Fixed yellow light time
    yellow_light_time = 5  # Assume yellow light is 5 seconds for each direction

    # Total cycle time
    total_cycle_time = 120  # Fixed total cycle of 120 seconds

    # Ensure that red light times are positive and proportional
    # Calculate total green light time used across all directions
    total_green_time = green_north + green_south + green_east + green_west + 4 * yellow_light_time

    # If total green and yellow time exceeds the total cycle time, cap it at the cycle time
    if total_green_time > total_cycle_time:
        total_green_time = total_cycle_time

    # Calculate available red light time for each direction
    red_north = total_cycle_time - (green_north + yellow_light_time)
    red_south = total_cycle_time - (green_south + yellow_light_time)
    red_east = total_cycle_time - (green_east + yellow_light_time)
    red_west = total_cycle_time - (green_west + yellow_light_time)

    return green_north, yellow_light_time, red_north, green_south, yellow_light_time, red_south, green_east, yellow_light_time, red_east, green_west, yellow_light_time, red_west

def main():
    user_data = get_user_input()

    # Predict signal times
    green_north, yellow_north, red_north, green_south, yellow_south, red_south, green_east, yellow_east, red_east, green_west, yellow_west, red_west = predict_signal_times(user_data)

    # Display the results
    print(f"\nFor North:")
    print(f"Green light time: {green_north:.2f} seconds")
    print(f"Yellow light time: {yellow_north:.2f} seconds")
    print(f"Red light time: {red_north:.2f} seconds")

    print(f"\nFor South:")
    print(f"Green light time: {green_south:.2f} seconds")
    print(f"Yellow light time: {yellow_south:.2f} seconds")
    print(f"Red light time: {red_south:.2f} seconds")

    print(f"\nFor East:")
    print(f"Green light time: {green_east:.2f} seconds")
    print(f"Yellow light time: {yellow_east:.2f} seconds")
    print(f"Red light time: {red_east:.2f} seconds")

    print(f"\nFor West:")
    print(f"Green light time: {green_west:.2f} seconds")
    print(f"Yellow light time: {yellow_west:.2f} seconds")
    print(f"Red light time: {red_west:.2f} seconds")

if __name__ == "__main__":
    main()
