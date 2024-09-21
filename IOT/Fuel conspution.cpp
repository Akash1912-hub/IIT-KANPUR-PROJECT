#include <iostream>
#include <vector>
#include <string>

// Simulated data structure for vehicle state
struct VehicleState {
    int currentGear;  // Current gear (1-5, 0 for neutral/reverse)
    double rpm;       // Engine RPM
    double speed;     // Vehicle speed in km/h
    bool suddenBrake; // Indicates if there was a sudden brake
    bool rapidAcceleration; // Indicates if there was rapid acceleration
};

// Function to analyze driving behavior
std::string analyzeDrivingBehavior(const VehicleState& state) {
    const double rpmThreshold = 3000.0; // RPM threshold for early gear shift
    const int maxGear = 5;               // Maximum gear

    std::string feedback;

    // Analyze RPM and gear shifting
    if (state.rpm > rpmThreshold && state.currentGear < maxGear) {
        feedback += "Shift to a higher gear for better fuel efficiency. ";
    } else if (state.rpm < (rpmThreshold - 1000) && state.currentGear > 1) {
        feedback += "Consider shifting to a lower gear to improve power. ";
    }

    // Analyze sudden braking
    if (state.suddenBrake) {
        feedback += "Avoid sudden braking; it can waste fuel. ";
    }

    // Analyze rapid acceleration
    if (state.rapidAcceleration) {
        feedback += "Avoid rapid acceleration; it increases fuel consumption. ";
    }

    // If no feedback was generated, the behavior is efficient
    if (feedback.empty()) {
        feedback = "Driving behavior is efficient.";
    }

    return feedback;
}

// Simulate a driving scenario
void simulateDriving() {
    // Simulated vehicle states
    std::vector<VehicleState> drivingData = {
        {2, 3200, 50, false, false}, // Gear 2, RPM 3200, normal driving
        {3, 2900, 40, true, false},  // Gear 3, RPM 2900, sudden brake
        {1, 4000, 30, false, true},   // Gear 1, RPM 4000, rapid acceleration
        {5, 2500, 60, false, false},  // Gear 5, RPM 2500, normal driving
        {4, 3100, 20, true, true}      // Gear 4, RPM 3100, sudden brake and rapid acceleration
    };

    for (const auto& state : drivingData) {
        std::cout << "Current Gear: " << state.currentGear 
                  << ", RPM: " << state.rpm 
                  << ", Speed: " << state.speed 
                  << " km/h, Sudden Brake: " << (state.suddenBrake ? "Yes" : "No") 
                  << ", Rapid Acceleration: " << (state.rapidAcceleration ? "Yes" : "No") 
                  << " -> ";
        std::cout << analyzeDrivingBehavior(state) << std::endl;
    }
}

int main() {
    simulateDriving();
    return 0;
}
