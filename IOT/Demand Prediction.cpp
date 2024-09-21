#include <iostream>
#include <vector>
#include <oneapi/dpl/execution>
#include <oneapi/dpl/algorithm>

// Simulating passenger sensor data collection
int getPassengerCount() {
    // For illustration, return dummy passenger count
    return rand() % 50 + 1;  // Random number between 1 and 50
}

void processPassengerData() {
    // Simulate collecting passenger data over time
    std::vector<int> passengerData(1000);
    for (int& count : passengerData) {
        count = getPassengerCount();
    }

    // Process the passenger data using oneAPI parallel execution
    oneapi::dpl::execution::par_unseq_policy policy;
    int totalPassengers = std::reduce(policy, passengerData.begin(), passengerData.end());
    
    std::cout << "Total passengers collected: " << totalPassengers << std::endl;
}

int main() {
    processPassengerData();
    return 0;
}
