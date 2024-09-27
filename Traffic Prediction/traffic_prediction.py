# Step 1: Install necessary libraries
!pip install pandas scikit-learn openpyxl

# Step 2: Import necessary libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Step 3: Load the dataset from the specified path
df = pd.read_excel('/content/Book2.xlsx')  # Load the Excel file

# Step 4: Display the first few rows of the DataFrame to understand its structure
print(df.head())

# Step 5: Preprocess the dataset
# Drop non-numeric columns and any unnecessary columns
X = df.drop(columns=['Vol', 'WktGeom', 'street', 'fromSt', 'toSt', 'Direction'])  # Features
y = df['Vol']  # Target variable

# Step 6: Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 7: Create and train the model
model = LinearRegression()
model.fit(X_train, y_train)

# Step 8: Make predictions on the training dataset
y_pred = model.predict(X_test)

# Step 9: Evaluate the model
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print("Mean Squared Error:", mse)
print("R-squared:", r2)

# Step 10: Provide input for prediction
# Prompt for input including SegmentID
print("\nEnter values for prediction:")
input_values = []
for column in X.columns:
    value = float(input(f"Enter value for {column}: "))  # Prompt user for input
    input_values.append(value)

# Convert input to DataFrame
input_df = pd.DataFrame([input_values], columns=X.columns)

# Step 11: Make a prediction based on user input
prediction = model.predict(input_df)

# Step 12: Display the prediction
print("Predicted Volume:", prediction[0])
