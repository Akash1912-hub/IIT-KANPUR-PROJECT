import cv2
import numpy as np
import requests
from retinaface import RetinaFace

# Firebase setup
firebase_url = 'https://ml-transport-1-default-rtdb.firebaseio.com/'  # Your Firebase Realtime Database URL
firebase_secret = 'ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk'  # Your Firebase Database secret

# Initialize video capture from the laptop camera
cap = cv2.VideoCapture(0)  # Change to 0 to use the laptop webcam

def update_firebase(face_count):
    # Define the URL to send data to Firebase
    firebase_update_url = f"{firebase_url}/face_count.json?auth={firebase_secret}"

    # Data to send
    data = {
        'face_count': face_count
    }

    # Make the POST request to Firebase to update the face count
    response = requests.put(firebase_update_url, json=data)
    
    if response.status_code == 200:
        print("Face count successfully updated in Firebase.")
    else:
        print(f"Failed to update Firebase. Status code: {response.status_code}")

while True:
    # Capture the frame from the laptop camera
    ret, frame = cap.read()
    
    if not ret:
        print("Failed to capture image from the laptop webcam")
        break

    # Perform face detection using RetinaFace
    detections = RetinaFace.detect_faces(frame)

    current_faces = []  # List to keep track of current frame detections (coordinates)

    # Loop through detected faces
    if isinstance(detections, dict):  # Check if any faces were detected
        for key, face_info in detections.items():
            face_box = face_info["facial_area"]
            x, y, x1, y1 = face_box

            # Draw the bounding box and label on the frame
            cv2.rectangle(frame, (x, y), (x1, y1), (0, 255, 0), 2)
            label = f"Face Detected"
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Add the face coordinates (centroid) to the current faces list
            centroid = ((x + x1) // 2, (y + y1) // 2)
            current_faces.append(centroid)

    # Count the number of faces detected in the current frame
    total_people_count = len(current_faces)
    
    # Update the face count in Firebase
    update_firebase(total_people_count)

    # Display the face count on the frame
    cv2.putText(frame, f'Total People Count: {total_people_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Show the output frame
    cv2.imshow("Face Detection", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close windows
cap.release()
cv2.destroyAllWindows()
