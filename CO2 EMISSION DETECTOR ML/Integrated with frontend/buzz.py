from flask import Flask, request, jsonify
import joblib
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the saved model and preprocessor
model = joblib.load('linear_regression_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json

    new_car = pd.DataFrame({
        'engine_size_cm3': [data['engine_size_cm3']],
        'power_ps': [data['power_ps']],
        'fuel': [data['fuel'].strip().capitalize()],
        'transmission_type': [data['transmission_type'].strip().capitalize()]
    })

    new_car_preprocessed = preprocessor.transform(new_car)
    predicted_co2 = model.predict(new_car_preprocessed)

    return jsonify({'predicted_co2_emissions': predicted_co2[0]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)