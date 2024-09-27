# AI-Based Public Transportation Optimization Project

## Overview
This project focuses on optimizing public transportation routes and schedules using AI, machine learning models, and IoT devices. The objective is to reduce fuel consumption, minimize carbon emissions, and maximize convenience for city residents.

## IoT Code Outputs
These outputs are provided for understanding purposes and demonstrate the data collection and processing capabilities of the system.

### 1. **GPS Module Data Collection & Processing:**
- **Current Location:** Latitude = 28.6139, Longitude = 77.2090 (New Delhi)
- **Total Distance Processed:** 4991.61 (arbitrary units for this simulation)

### 2. **Passenger Sensor Data Collection:**
- **Total Passengers Collected:** 25,079

### 3. **Traffic Sensor Data Collection:**
- **Average Traffic Speed:** 48.82 km/h

### 4. **Schedule Optimization with GPS and Passenger Data:**
- **Total Passengers Processed:** 25,495

### 5. **Fuel Consumption Analysis:**
- **Current Gear:** 2, **RPM:** 3200, **Speed:** 50 km/h, **Sudden Brake:** No, **Rapid Acceleration:** No  
  _Recommendation:_ Shift to a higher gear for better fuel efficiency.

- **Current Gear:** 3, **RPM:** 2900, **Speed:** 40 km/h, **Sudden Brake:** Yes, **Rapid Acceleration:** No  
  _Recommendation:_ Avoid sudden braking; it can waste fuel.

- **Current Gear:** 1, **RPM:** 4000, **Speed:** 30 km/h, **Sudden Brake:** No, **Rapid Acceleration:** Yes  
  _Recommendation:_ Avoid rapid acceleration; it increases fuel consumption.

- **Current Gear:** 5, **RPM:** 2500, **Speed:** 60 km/h, **Sudden Brake:** No, **Rapid Acceleration:** No  
  _Recommendation:_ Driving behavior is efficient.

- **Current Gear:** 4, **RPM:** 3100, **Speed:** 20 km/h, **Sudden Brake:** Yes, **Rapid Acceleration:** Yes  
  _Recommendation:_ Avoid sudden braking and rapid acceleration; both increase fuel consumption.

---

## Features
- **Traffic Prediction:** Predicts traffic conditions using machine learning models.
- **Route Optimization:** Reinforcement learning-based system to optimize bus routes.
- **Demand Prediction:** Forecasts passenger demand using time-series models.
- **CO2 Emissions Modeling:** Tracks and reduces carbon emissions.

## Tech Stack
- **IoT Devices:** ESP32/Arduino for data collection
- **Machine Learning Models:** ARIMA, LSTM, Gradient Boosting, Random Forest
- **Cloud Platforms:** Google Cloud, AWS, Intel oneAPI

---

We have completed **85%** of the project and are looking forward to delivering a fully functional product soon. Stay tuned for more updates!
