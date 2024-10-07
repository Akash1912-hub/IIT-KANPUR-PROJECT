from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
from scipy.sparse import hstack, csr_matrix

# Load the trained model and preprocessors from pickle files
with open('traffic_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('preprocessors.pkl', 'rb') as preprocessors_file:
    preprocessors = pickle.load(preprocessors_file)

one_hot_encoder = preprocessors['one_hot_encoder']
ordinal_encoder = preprocessors['ordinal_encoder']
imputer = preprocessors['imputer']
scaler = preprocessors['scaler']

# Create Flask app
app = Flask(__name__)

# Route to serve the HTML file
@app.route('/')
def index():
    return render_template('intex.html')

# Route to handle prediction requests
@app.route('/predict', methods=['POST'])
def predict():
    # Get the JSON data from the request
    data = request.json

    # Convert the input data into a DataFrame
    input_data = pd.DataFrame([data])

    # Preprocess the input data
    low_card_encoded = one_hot_encoder.transform(input_data[['Boro', 'Direction']])
    high_card_encoded = ordinal_encoder.transform(input_data[['street', 'fromSt', 'toSt', 'SegmentID']])
    input_numeric = input_data[['Yr', 'M', 'D', 'HH', 'MM']].to_numpy()

    # Combine encoded features
    input_encoded_combined = hstack([low_card_encoded, csr_matrix(high_card_encoded), csr_matrix(input_numeric)])

    # Impute missing values and scale features
    input_imputed = imputer.transform(input_encoded_combined)
    input_scaled = scaler.transform(input_imputed)

    # Make prediction
    prediction = model.predict(input_scaled)

    # Assume we have coordinates in the request (for visualization purposes)
    coordinates = {
        "latitude": data.get("latitude", 40.7128),  # Example default: NYC latitude
        "longitude": data.get("longitude", -74.0060)  # Example default: NYC longitude
    }

    return jsonify({'predicted_traffic_volume': prediction[0], 'coordinates': coordinates})

if __name__ == '__main__':
    app.run(debug=True)
