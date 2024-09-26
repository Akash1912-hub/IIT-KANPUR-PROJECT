
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score


df = pd.read_csv('/content/uk_gov_data_dense_preproc (1).csv', encoding='ISO-8859-1')

X = df[['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']]  
y = df['co2_emissions_gPERkm'] 


X = pd.get_dummies(X, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)


y_pred = model.predict(X_test)
print('Mean Absolute Error (MAE):', mean_absolute_error(y_test, y_pred))
print('R-squared:', r2_score(y_test, y_pred))

def predict_emissions():
    engine_size = float(input("Enter the engine size in cm³ (e.g., 2000): "))
    power_ps = float(input("Enter the power in PS (e.g., 150): "))
    fuel = input("Enter the fuel type (Petrol or Diesel): ")
    transmission = input("Enter the transmission type (Manual or Automatic): ")

    new_car = pd.DataFrame({
        'engine_size_cm3': [engine_size],
        'power_ps': [power_ps],
        'fuel': [fuel],
        'transmission_type': [transmission]
    })

    new_car = pd.get_dummies(new_car, drop_first=True)
    new_car = new_car.reindex(columns=X_train.columns, fill_value=0)

    predicted_co2 = model.predict(new_car)
    print(f"Predicted CO2 Emissions for the new car: {predicted_co2[0]:.2f} grams per kilometer")


predict_emissions()
