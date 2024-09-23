from flask import Flask, request, render_template
import joblib
import pandas as pd

app = Flask(__name__)

# Load the trained model
model = joblib.load('model.pkl')

# Create a function to preprocess the input data
def preprocess_input(data):
    df = pd.DataFrame([data])

    # Encode categorical features
    categorical_cols = ['DirectionRef', 'PublishedLineName', 'OriginName', 'DestinationName', 'ExpectedArrivalTime', 'ScheduledArrivalTime']
    
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype('category').cat.codes
    
    # Ensure the correct feature order
    expected_order = ['DirectionRef', 'PublishedLineName', 'OriginName', 'OriginLat', 'OriginLong',
                      'DestinationName', 'DestinationLat', 'DestinationLong', 
                      'VehicleLocation.Latitude', 'VehicleLocation.Longitude', 
                      'ExpectedArrivalTime', 'ScheduledArrivalTime', 'hour', 'day']
    
    return df[expected_order]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get the form data with default values to handle missing fields
        data = {
            'DirectionRef': request.form.get('DirectionRef', ''),
            'PublishedLineName': request.form.get('PublishedLineName', ''),
            'OriginName': request.form.get('OriginName', ''),
            'OriginLat': float(request.form.get('OriginLat', 0.0)),
            'OriginLong': float(request.form.get('OriginLong', 0.0)),
            'DestinationName': request.form.get('DestinationName', ''),
            'DestinationLat': float(request.form.get('DestinationLat', 0.0)),
            'DestinationLong': float(request.form.get('DestinationLong', 0.0)),
            'VehicleLocation.Latitude': float(request.form.get('VehicleLocation.Latitude', 0.0)),
            'VehicleLocation.Longitude': float(request.form.get('VehicleLocation.Longitude', 0.0)),
            'ExpectedArrivalTime': request.form.get('ExpectedArrivalTime', ''),
            'ScheduledArrivalTime': request.form.get('ScheduledArrivalTime', ''),
            'hour': int(request.form.get('hour', 0)),
            'day': int(request.form.get('day', 0)),
        }
        
        # Preprocess the input data
        processed_data = preprocess_input(data)

        # Make a prediction
        prediction = model.predict(processed_data)

        return render_template('index.html', prediction=prediction[0])

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
