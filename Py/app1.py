import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load the dataset
df = pd.read_csv(r"C:/Users/priya/Downloads/uk_gov_data_dense_preproc.csv", encoding='ISO-8859-1')
X = df[['engine_size_cm3', 'power_ps', 'fuel', 'transmission_type']]
y = df['co2_emissions_gPERkm']

# Split the dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define preprocessing for numeric and categorical features
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

# Combine preprocessors in a column transformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)

# Preprocess the training and test data
X_train_preprocessed = preprocessor.fit_transform(X_train)
X_test_preprocessed = preprocessor.transform(X_test)

# Train a Scikit-learn Linear Regression model
from sklearn.linear_model import LinearRegression
sklearn_model = LinearRegression()
sklearn_model.fit(X_train_preprocessed, y_train)

# Save the model and preprocessor to .pkl files
joblib.dump(sklearn_model, 'linear_regression_model.pkl')
joblib.dump(preprocessor, 'preprocessor.pkl')

# Evaluate the Scikit-learn model
y_pred_sklearn = sklearn_model.predict(X_test_preprocessed)
mae_sklearn = mean_absolute_error(y_test, y_pred_sklearn)
r2_sklearn = r2_score(y_test, y_pred_sklearn)
logging.info('Scikit-learn Model - Mean Absolute Error (MAE): %s', mae_sklearn)
logging.info('Scikit-learn Model - R-squared: %s', r2_sklearn)
