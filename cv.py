import cv2
import numpy as np
import os
import requests
from datetime import datetime

# Load pre-trained model and config files for vehicle detection (MobileNet SSD)
net = cv2.dnn.readNetFromCaffe('/Users/kirthika/Downloads/deploy.prototxt', '/Users/kirthika/Downloads/mobilenet_iter_73000.caffemodel')

# Initialize the webcam (0 for the default camera)
cap = cv2.VideoCapture(0)

# Firebase setup (if needed)
firebase_url = 'https://ml-transport-1-default-rtdb.firebaseio.com/'
firebase_secret = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'

# File to store vehicle count for the south direction
vehicle_count_file = "vehicle_count_south.txt"

# Function to update vehicle count in a file (south direction)
def update_vehicle_count(vehicle_count):
    with open(vehicle_count_file, 'w') as f:
        f.write(str(vehicle_count))

# Initialize the CSV file for logging vehicle detection
csv_filename = "VehicleCount.csv"
if csv_filename in os.listdir():
    os.remove(csv_filename)

with open(csv_filename, 'w') as f:
    f.write("Vehicle,Time\n")

# Function to log vehicle detection
def log_vehicle_count(count):
    with open(csv_filename, 'a') as f:
        now = datetime.now()
        dt_string = now.strftime('%H:%M:%S')
        f.write(f'Vehicle{count},{dt_string}\n')

while True:
    # Capture frame from the webcam
    ret, img = cap.read()
    
    if not ret:
        print("Failed to capture image from webcam")
        break

    # Prepare the image for the object detection model
    (h, w) = img.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    
    # Get detections from the network
    detections = net.forward()

    vehicle_count = 0  # Reset vehicle count for this frame

    # Loop over the detections and filter for vehicles
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        
        # Filter out weak detections
        if confidence > 0.5:
            idx = int(detections[0, 0, i, 1])

            # Check if the object detected is a vehicle (adjust based on your dataset)
            if idx == 7:  # Car class index in MobileNet SSD
                vehicle_count += 1
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Draw bounding box around the vehicle
                cv2.rectangle(img, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.putText(img, "Car", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Log the vehicle detection
    log_vehicle_count(vehicle_count)

    # Save the vehicle count for the south direction to a file
    update_vehicle_count(vehicle_count)

    # Display the total vehicle count on the frame
    cv2.putText(img, f"Total Vehicles: {vehicle_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Show the frame with detections
    cv2.imshow('Vehicle Detection', img)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
