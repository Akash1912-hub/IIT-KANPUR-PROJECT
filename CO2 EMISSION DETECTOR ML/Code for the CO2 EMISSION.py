import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
import daal4py as d4p
import numpy as np
import warnings
warnings.filterwarnings('ignore')
df = pd.read_csv("/content/uk_gov_data_sparse_preproc (1).csv", encoding='ISO-8859-1')
X = df[['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']]
y = df['co2_emissions_gPERkm']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


numeric_features = ['engine_size_cm3', 'power_ps']
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),  
    ('scaler', StandardScaler())                  
])

categorical_features = ['fuel', 'transmission_type']
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),  
    ('encoder', OneHotEncoder(drop='first'))               
])


preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)


X_train_preprocessed = preprocessor.fit_transform(X_train)
X_test_preprocessed = preprocessor.transform(X_test)

X_train_np = X_train_preprocessed.astype('float64')
X_test_np = X_test_preprocessed.astype('float64')

y_train_np = y_train.values.reshape(-1, 1).astype('float64')
y_test_np = y_test.values.reshape(-1, 1).astype('float64')

linear_regression_train = d4p.linear_regression_training()
linear_regression_model = linear_regression_train.compute(X_train_np, y_train_np)
linear_regression_predict = d4p.linear_regression_prediction()

y_pred = linear_regression_predict.compute(X_test_np, linear_regression_model.model).prediction

mae = mean_absolute_error(y_test_np, y_pred)
r2 = r2_score(y_test_np, y_pred)
print('Mean Absolute Error (MAE):', mae)
print('R-squared:', r2)
from sklearn.linear_model import LinearRegression
sklearn_model = LinearRegression()
sklearn_model.fit(X_train_preprocessed, y_train)
def predict_emissions_sklearn():
    engine_size = float(input("Enter the engine size in cm³ : "))
    power_ps = float(input("Enter the power in PS : "))
    fuel = input("Enter the fuel type : ").strip().capitalize()
    transmission = input("Enter the transmission type : ").strip().capitalize()
    new_car = pd.DataFrame({
        'engine_size_cm3': [engine_size],
        'power_ps': [power_ps],
        'fuel': [fuel],
        'transmission_type': [transmission]
    })
    new_car_preprocessed = preprocessor.transform(new_car)
    predicted_co2 = sklearn_model.predict(new_car_preprocessed)
    print(f"Predicted CO2 Emissions for the new car: {predicted_co2[0]:.2f} grams per kilometer")
y_pred_sklearn = sklearn_model.predict(X_test_preprocessed)
mae_sklearn = mean_absolute_error(y_test, y_pred_sklearn)
r2_sklearn = r2_score(y_test, y_pred_sklearn)
print('Scikit-learn Model - Mean Absolute Error (MAE):', mae_sklearn)
print('Scikit-learn Model - R-squared:', r2_sklearn)
predict_emissions_sklearn()
