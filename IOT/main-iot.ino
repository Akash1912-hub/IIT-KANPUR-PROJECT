#include <Wire.h>

#include <TinyGPS++.h>

#include <HardwareSerial.h>

#include <MPU6050.h>

#include <FirebaseESP32.h>

#include <WiFi.h>





const char* carID = "CAR_001";





TinyGPSPlus gps;

HardwareSerial gpsSerial(2); // GPS Serial on pins 2





volatile int holeCount = 0; // Use volatile since it's accessed in an ISR

unsigned long lastRPMTime = 0;

float rpm = 0;





int pressurePin = A0; // Analog pin for brake pressure sensor

int brakePressure = 0;



int irA = 3; // IR sensor A

int irB = 4; // IR sensor B

int demandCount = 0;





const char* ssid = "Gokul";

const char* password = "gothagomma";





FirebaseData firebaseData;

FirebaseAuth auth;

FirebaseConfig config;





MPU6050 mpu;

const float alpha = 0.9;

int16_t ax, ay, az;

float accelerationMagnitude = 0;

float speed = 0;

unsigned long lastSpeedTime = 0;



void setup() {

Serial.begin(115200);



 // Initialize GPS

gpsSerial.begin(9600);



 // Initialize MPU6050

Wire.begin();

mpu.initialize();

if (!mpu.testConnection()) {

Serial.println("MPU6050 connection failed");

while (1);

}



 // Initialize RPM sensor (interrupt pin 2)

pinMode(2, INPUT);

attachInterrupt(digitalPinToInterrupt(2), countHoles, FALLING);



 // Initialize IR sensors

pinMode(irA, INPUT);

pinMode(irB, INPUT);



 // Connect to Wi-Fi

connectToWiFi();



 // Set up Firebase config

config.host = "ml-transport-1-default-rtdb.firebaseio.com"; // Firebase Realtime Database URL

config.signer.tokens.legacy_token = "ItQZCGVw8HvBMKM03oVJKRfZAWAi6112wUHIwdXk"; // Firebase database secret



 // Initialize Firebase

Firebase.begin(&config, &auth);

Firebase.reconnectWiFi(true);



 // Initialize timing

lastSpeedTime = millis();

}



void loop() {

 // Handle GPS and send data to Firebase every 5 seconds

if (millis() - lastSpeedTime > 5000) {

if (gpsSerial.available()) {

while (gpsSerial.available()) {

gps.encode(gpsSerial.read());

}

if (gps.location.isValid()) {

String latitude = String(gps.location.lat(), 6);

String longitude = String(gps.location.lng(), 6);



 // Send data to Firebase

sendDataToFirebase(latitude, longitude, rpm, brakePressure, demandCount, speed);

}

}

lastSpeedTime = millis();

}



 // Calculate RPM every 1 second

if (millis() - lastRPMTime > 1000) {

calculateRPM();

lastRPMTime = millis();

}



 // Read brake pressure sensor

brakePressure = analogRead(pressurePin);



 // Handle demand prediction with IR sensors

handleIRSensors();



 // Calculate speed using MPU6050

calculateSpeed();



 // Print all status information

printStatus();

}



// Function to count holes for RPM

void countHoles() {

holeCount++;

}



// Function to calculate RPM based on hole counts

void calculateRPM() {

rpm = (holeCount / 20.0) * 60; // Assuming 20 holes per revolution

holeCount = 0; // Reset hole count after each second

}



// Function to calculate speed using MPU6050

void calculateSpeed() {

int16_t rawAx, rawAy, rawAz; // Use separate variables for raw values

mpu.getAcceleration(&rawAx, &rawAy, &rawAz);



 // Apply low-pass filter to smooth readings

ax = alpha * ax + (1 - alpha) * rawAx;

ay = alpha * ay + (1 - alpha) * rawAy;

az = alpha * az + (1 - alpha) * rawAz;



 // Calculate acceleration magnitude

accelerationMagnitude = sqrt(pow(ax, 2) + pow(ay, 2) + pow(az, 2)) / 16384.0;



 // Calculate speed (integrate acceleration)

unsigned long currentTime = millis();

float deltaTime = (currentTime - lastSpeedTime) / 1000.0;



 // Limit integration only if acceleration exceeds a certain threshold

if (accelerationMagnitude > 0.1) {

speed += accelerationMagnitude * deltaTime;

} else {

speed = max(speed - 0.1 * deltaTime, 0.0); // Gradually reduce speed if no acceleration

}



lastSpeedTime = currentTime;

}



// Function to handle IR sensors for demand prediction

void handleIRSensors() {

static bool previousStateA = HIGH; // Previous state for IR A

static bool previousStateB = HIGH; // Previous state for IR B



int irAState = digitalRead(irA);

int irBState = digitalRead(irB);



 // Check for transition from HIGH to LOW on IR A

if (previousStateA == HIGH && irAState == LOW) {

demandCount++; // Increment demand count when entering from A to B

Serial.println("Passenger entered: Object moved from A to B");

}



 // Check for transition from HIGH to LOW on IR B

if (previousStateB == HIGH && irBState == LOW) {

if (demandCount > 0) {

demandCount--; // Decrement demand count when exiting from B to A

Serial.println("Passenger exited: Object moved from B to A");

}

}



 // Update previous states

previousStateA = irAState;

previousStateB = irBState;

}



// Function to send data to Firebase Realtime Database

void sendDataToFirebase(String latitude, String longitude, float rpm, int brakePressure, int demand, float speed) {

if (WiFi.status() == WL_CONNECTED) {

String path = "/vehicles/" + String(carID);



if (Firebase.setString(firebaseData, path + "/latitude", latitude)) {

Serial.println("Latitude updated");

} else {

Serial.println("Failed to update Latitude: " + firebaseData.errorReason());

}



if (Firebase.setString(firebaseData, path + "/longitude", longitude)) {

Serial.println("Longitude updated");

} else {

Serial.println("Failed to update Longitude: " + firebaseData.errorReason());

}



if (Firebase.setFloat(firebaseData, path + "/rpm", rpm)) {

Serial.println("RPM updated");

} else {

Serial.println("Failed to update RPM: " + firebaseData.errorReason());

}



if (Firebase.setInt(firebaseData, path + "/brakePressure", brakePressure)) {

Serial.println("Brake Pressure updated");

} else {

Serial.println("Failed to update Brake Pressure: " + firebaseData.errorReason());

}



if (Firebase.setInt(firebaseData, path + "/demand", demand)) {

Serial.println("Demand Count updated");

} else {

Serial.println("Failed to update Demand Count: " + firebaseData.errorReason());

}



if (Firebase.setFloat(firebaseData, path + "/speed", speed)) {

Serial.println("Speed updated");

} else {

Serial.println("Failed to update Speed: " + firebaseData.errorReason());

}



} else {

Serial.println("WiFi not connected");

}

}



// Function to connect to Wi-Fi

void connectToWiFi() {

Serial.println("Connecting to Wi-Fi...");

WiFi.begin(ssid, password);

unsigned long startAttemptTime = millis();

while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 30000) {

delay(1000);

Serial.println("Connecting...");

}

if (WiFi.status() == WL_CONNECTED) {

Serial.println("Connected to Wi-Fi");

} else {

Serial.println("Failed to connect to Wi-Fi");

}

}



// Function to print status information

void printStatus() {

String latitude = gps.location.isUpdated() ? String(gps.location.lat(), 6) : "12.9716";

String longitude = gps.location.isUpdated() ? String(gps.location.lng(), 6) : "77.5946";



Serial.print("Car ID: "); Serial.print(carID);

Serial.print(", Latitude: "); Serial.print(latitude);

Serial.print(", Longitude: "); Serial.print(longitude);

Serial.print(", Speed: "); Serial.print(speed);

Serial.print(" m/s, RPM: "); Serial.print(rpm);

Serial.print(", Brake Pressure: "); Serial.print(brakePressure);

Serial.print(", Demand Count: "); Serial.println(demandCount);

}
