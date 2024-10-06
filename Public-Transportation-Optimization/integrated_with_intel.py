import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input, Dropout, BatchNormalization, LeakyReLU
import joblib
import daal4py as d4p  

def preprocess_data(df):
    print("Starting data preprocessing...")
    df = df.drop_duplicates()
    print(f"Duplicates removed, remaining records: {len(df)}")
    
    df['RecordedAtTime'] = pd.to_datetime(df['RecordedAtTime'])
    
    df['hour'] = df['RecordedAtTime'].dt.hour
    df['day'] = df['RecordedAtTime'].dt.dayofweek
    
    
    df = df.drop(columns=['RecordedAtTime', 'VehicleRef', 'NextStopPointName', 'ArrivalProximityText'])
    

    categorical_cols = df.select_dtypes(include=['object']).columns
    label_encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le
    
    
    if df.isnull().sum().sum() > 0:
        print("NaN values found in the dataset. Handling missing values...")
        df.fillna(df.mean(), inplace=True)
    
    print("Data preprocessing completed.")
    return df

def train_dnn_model(X_train, y_train):
   
    print("Building and training the DNN model with TensorFlow...")
    model = Sequential()
    model.add(Input(shape=(X_train.shape[1],)))
    model.add(Dense(256))
    model.add(LeakyReLU(alpha=0.01))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))

    model.add(Dense(128))
    model.add(LeakyReLU(alpha=0.01))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))

    model.add(Dense(64))
    model.add(LeakyReLU(alpha=0.01))
    model.add(BatchNormalization())
    model.add(Dropout(0.3))

    model.add(Dense(1))  

    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
   
    early_stopping = tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.2, min_lr=1e-6)

    model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2, callbacks=[early_stopping, reduce_lr])
    print("Model training completed.")

    model.save('model.h5')
    print("DNN model saved as model.h5.")

def train_oneDAL_random_forest(X_train, y_train):
   
    print("Building and training the RandomForest model with Intel oneDAL...")
    rf_train = d4p.decision_forest_regression_training(nTrees=100)
    train_result = rf_train.compute(X_train, y_train)
    model = train_result.model
    print("RandomForest model training completed.")

   
    joblib.dump(model, 'random_forest_model.pkl')
    print("RandomForest model saved as random_forest_model.pkl.")

def train_model():
    
    data = pd.read_csv('/content/mta_1712.csv', on_bad_lines="skip")
    data = preprocess_data(data)

  
    sample_data = data.sample(frac=0.1, random_state=42)

   
    X = sample_data.drop(columns=['DistanceFromStop'])
    y = sample_data['DistanceFromStop']
 
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    
    joblib.dump(scaler, 'scaler.pkl')
    print("Scaler saved as scaler.pkl.")

   
    train_dnn_model(X_train, y_train)

    train_oneDAL_random_forest(X_train, y_train)

if __name__ == '__main__':
    train_model()
