import pandas as pd
import numpy as np
import pickle
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from scipy.sparse import hstack, csr_matrix

df = pd.read_csv(r"D:\Dataset\Automated_Traffic_Volume_Counts.csv", nrows=10**6)

feature_columns = ['Boro', 'Yr', 'M', 'D', 'HH', 'MM', 'SegmentID', 'street', 'fromSt', 'toSt', 'Direction']
target_column = 'Vol'

df = df.dropna(subset=[target_column])

X = df[feature_columns]
y = df[target_column]

low_cardinality_features = ['Boro', 'Direction']
high_cardinality_features = ['street', 'fromSt', 'toSt', 'SegmentID']
numeric_features = ['Yr', 'M', 'D', 'HH', 'MM']

one_hot_encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=True)
ordinal_encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)

low_card_encoded = one_hot_encoder.fit_transform(X[low_cardinality_features])
high_card_encoded = ordinal_encoder.fit_transform(X[high_cardinality_features])
X_numeric = X[numeric_features].to_numpy()

X_encoded_combined = hstack([low_card_encoded, csr_matrix(high_card_encoded), csr_matrix(X_numeric)])

imputer = SimpleImputer(strategy='most_frequent')
X_imputed = imputer.fit_transform(X_encoded_combined)

scaler = StandardScaler(with_mean=False)
X_imputed = scaler.fit_transform(X_imputed)

X_train, X_test, y_train, y_test = train_test_split(X_imputed, y, test_size=0.2, random_state=42)

sgd_regressor = SGDRegressor(max_iter=500, tol=1e-2)
sgd_regressor.fit(X_train, y_train)

with open('traffic_model.pkl', 'wb') as model_file:
    pickle.dump(sgd_regressor, model_file)

with open('preprocessors.pkl', 'wb') as preprocessors_file:
    pickle.dump({
        'one_hot_encoder': one_hot_encoder,
        'ordinal_encoder': ordinal_encoder,
        'imputer': imputer,
        'scaler': scaler
    }, preprocessors_file)
