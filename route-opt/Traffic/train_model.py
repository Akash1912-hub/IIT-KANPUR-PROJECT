import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# Load your traffic data
data = pd.read_csv(r'C:\Users\mrvan\OneDrive\Desktop\New folder\traffic_model\trafiic_data.csv')

# Prepare your features and labels
X = data[['feature1', 'feature2']]  # Replace with your actual features
y = data['traffic_volume']  # Target variable

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Train a linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the model
joblib.dump(model, 'traffic_model.pkl')

print("Model trained and saved as traffic_model.pkl")
