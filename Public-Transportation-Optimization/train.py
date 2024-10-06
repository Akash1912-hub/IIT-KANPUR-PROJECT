import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.preprocessing import LabelEncoder

def preprocess_data(df):
    print("Starting data preprocessing...")
    df = df.drop_duplicates()
    print(f"Duplicates removed, remaining records: {len(df)}")
    
    # Convert 'RecordedAtTime' to datetime
    df['RecordedAtTime'] = pd.to_datetime(df['RecordedAtTime'])
    # Extract features like hour, day, etc.
    df['hour'] = df['RecordedAtTime'].dt.hour
    df['day'] = df['RecordedAtTime'].dt.dayofweek
    
    # Drop unnecessary columns
    df = df.drop(columns=['RecordedAtTime', 'VehicleRef', 'NextStopPointName', 'ArrivalProximityText'])
    
    # Encode categorical features
    categorical_cols = df.select_dtypes(include=['object']).columns
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    
    # Handle NaN values
    if df.isnull().sum().sum() > 0:
        print("NaN values found in the dataset. Handling missing values...")
        df.fillna(df.mean(), inplace=True)
    
    print("Data preprocessing completed.")
    return df

def train_model():
    # Load the dataset
    data = pd.read_csv('data/raw/mta_1706.csv', on_bad_lines="skip")
    data = preprocess_data(data)

    # Sample the data (10% of the original)
    sample_data = data.sample(frac=0.01, random_state=42)

    # Split the data
    X = sample_data.drop(columns=['DistanceFromStop'])
    y = sample_data['DistanceFromStop']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Print the order of features used in training
    feature_order = X_train.columns.tolist()
    print("Feature order for training:", feature_order)

    # Train a model with parallel processing
    print("Training the model...")
    model = RandomForestRegressor(n_jobs=-1, n_estimators=100)  # Using 100 trees
    model.fit(X_train, y_train)
    print("Model training completed.")

    # Save the model
    joblib.dump(model, 'model.pkl')
    print("Model saved as model.pkl.")

if __name__ == '__main__':
    train_model()
