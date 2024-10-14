from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
from flask_cors import CORS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# Load the model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    required_fields = ['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing {field}'}), 400

    try:
        new_car = pd.DataFrame({
            'engine_size_cm3': [data['engine_size_cm3']],
            'power_ps': [data['power_ps']],
            'fuel': [data['fuel'].strip().capitalize()],
            'transmission_type': [data['transmission_type'].strip().capitalize()]
        })

        new_car_preprocessed = preprocessor.transform(new_car)
        predicted_co2 = model.predict(new_car_preprocessed)

        return jsonify({'predicted_co2_emissions': predicted_co2[0]})
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
