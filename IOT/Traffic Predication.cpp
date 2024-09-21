#include <iostream>
#include <vector>
#include <random>
#include <oneapi/dpl/execution>
#include <oneapi/dpl/algorithm>

// Simulating traffic sensor data collection
double getTrafficData() {
    // Random traffic data (e.g., vehicle speed in km/h)
    return rand() % 100 + 1; // Random speed between 1 and 100
}

void processTrafficData() {
    // Simulate collecting traffic data over time
    std::vector<double> trafficData(1000);
    for (double& speed : trafficData) {
        speed = getTrafficData();
    }

    // Using Intel oneAPI to process the traffic data efficiently
    oneapi::dpl::execution::par_unseq_policy policy;
    double avgSpeed = std::reduce(policy, trafficData.begin(), trafficData.end()) / trafficData.size();
    
    std::cout << "Average traffic speed processed: " << avgSpeed << " km/h" << std::endl;
}

int main() {
    processTrafficData();
    return 0;
}
