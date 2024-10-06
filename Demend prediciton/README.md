"Demand prediction"this need to only be executed in the "GOOGLE COLAB" not in any compiler like Visual Studio . 
The successfully integrated with one dal and one dnn


Overview
This ML predicts:
- Fuel consumption
- Taxi demand by hour
- Taxi fare based on trip details and location
- Historical peak hour demand

Features
- Predict fuelThis is the code of the   consumption using trip distance, duration, and passenger count.
- Estimate taxi demand for a specific pickup hour.
- Calculate taxi fare using distance, duration, passenger count, longitude, and latitude.
- Show historical demand for a specified hour.


#Sample output
-Enter trip details for fuel consumption prediction:
-Trip Distance (in miles): 5
-Trip Duration (in minutes): 20
-Passenger Count: 2
-Predicted Fuel Consumption: 0.75 gallons
-Enter Pickup Hour (0-23) for Demand Prediction: 8
-Predicted Demand at Hour 8: 1010.30 trips
-Enter trip details for fare prediction:
-Trip Distance (in miles): 5
-Trip Duration (in minutes): 20
-Passenger Count: 5
-Pickup Longitude: -73.9857
-Pickup Latitude: 40.7484
-Predicted Taxi Fare: $22.47
-Enter Pickup Hour (0-23) for Peak Hour Prediction: 8
-Historical Demand at Hour 8: 1125 trips
