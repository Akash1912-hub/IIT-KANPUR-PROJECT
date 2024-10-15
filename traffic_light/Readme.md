**Traffic Signal Timing Optimization using Computer Vision (CV) and Machine Learning (ML)**.

This repository contains the code and models for optimizing traffic signal timing using vehicle counts, time of day, and day of the week. The system predicts the optimal **green**, **yellow**, and **red light** durations for each direction (North, South, East, West) at an intersection, based on real-time traffic data and historical patterns. 

The goal of this project is to dynamically adjust signal timings to reduce waiting times at traffic intersections, providing longer green lights for high-traffic directions and reducing congestion.

## Features
- **Vehicle Detection**: Uses machine learning to predict signal timings based on vehicle counts.
- **Custom Timing Adjustments**: Dynamically adjusts **green**, **yellow**, and **red light** durations based on traffic volume.
- **Cycle Time Balancing**: Ensures each direction's light cycle is balanced to avoid excessive delays.
- **Computer Vision (Future Work)**: Integration with computer vision to detect vehicles in real-time (e.g., using cameras or other sensors).

## Table of Contents
- [Introduction](#introduction)
- [Dataset](#dataset)
- [Model Architecture](#model-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Future Work](#future-work)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Traffic congestion is a significant problem in urban areas, leading to delays, pollution, and wasted time. Traditional traffic signals operate on fixed cycles, which do not account for varying traffic volumes throughout the day. This project uses **machine learning (ML)** to predict traffic signal timings dynamically based on traffic conditions, reducing wait times and optimizing traffic flow.

In future development stages, the project will integrate **computer vision (CV)** to detect vehicles in real-time using traffic cameras or sensors, further enhancing traffic signal optimization.

### How It Works:
- The system predicts **green light** times for each direction based on the number of vehicles approaching the intersection.
- **Yellow light** times are fixed at 5 seconds for all directions.
- **Red light** times are calculated to balance the total cycle time (120 seconds) across all directions.
- In future work, **computer vision** will be used to detect vehicles, providing real-time traffic input to the system.

## Dataset

The dataset used for this project is synthetic and includes:
- **Time of day**: (0-23), representing the hour of the day.
- **Day of the week**: (1-7), where 1 is Monday and 7 is Sunday.
- **Vehicle counts**: Random values between 0 and 100 for each direction (North, South, East, West).

The green light time for each direction is calculated based on the vehicle count, ranging from **30 to 90 seconds**. The yellow light is fixed at **5 seconds**, and the red light is calculated dynamically based on the remaining cycle time.

## Model Architecture

The machine learning model uses a **fully connected neural network** built with **TensorFlow** and **Keras**. Separate models are trained for each direction (North, South, East, West) to predict the green light time based on vehicle counts.

**Model Structure**:
- Input: Time of day, day of the week, vehicle counts for each direction.
- Layers:
  - Dense layer with 64 neurons and ReLU activation.
  - Dense layer with 32 neurons and ReLU activation.
  - Output layer with 1 neuron (predicted green light time).
- Optimizer: Adam
- Loss: Mean Squared Error (MSE)

The red light time is calculated based on the remaining time after subtracting the green and yellow light times.

## Installation

To run this project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Akash1912-hub/IIT-KANPUR-PROJECT/main/traffic_light.git
   ```

2. **Navigate to the project directory**:
   ```bash
   cd traffic_light
   ```

3. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

4. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Download the dataset**:
   - The dataset is generated within the script, so you can simply run the script and it will create the dataset for you.

## Usage

To run the traffic signal optimization model, follow these steps:

1. **Run the model**:
   ```bash
   python traffic_signal_model.py
   ```

2. **Provide input**:
   The program will prompt you to input the following information:
   - **Time of day**: Enter the current hour (0-23).
   - **Day of the week**: Enter the day of the week (1-7, where 1 is Monday).
   - **Vehicle count for each direction**: Enter the number of vehicles for North, South, East, and West directions.

3. **Output**:
   The program will output the **green**, **yellow**, and **red light** times for each direction based on the vehicle count and traffic conditions.

Example:
```bash
Enter time of day (0-23): 12
Enter day of week (1-7): 5
Enter vehicle count (north): 25
Enter vehicle count (south): 32
Enter vehicle count (east): 45
Enter vehicle count (west): 11

For North:
Green light time: 56.08 seconds
Yellow light time: 5.00 seconds
Red light time: 58.92 seconds
...
```

## Future Work

The following improvements are planned for future versions:
1. **Computer Vision Integration**: Use camera feeds or video streams to detect vehicle counts in real-time using **OpenCV** or other CV libraries.
2. **Real-time Data Processing**: Integrate with real-world data sources (e.g., sensors, traffic cameras) for real-time signal optimization.
3. **Advanced Models**: Experiment with more advanced models, such as **reinforcement learning**, for more complex traffic scenarios.

## Contributing

If you'd like to contribute to this project, feel free to fork the repository and submit a pull request. Contributions can include bug fixes, new features, or documentation improvements.

1. Fork the repo
2. Create a new branch (`git checkout -b feature-branch`)
3. Make changes and commit (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature-branch`)
5. Open a pull request

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
```

### Notes:
- Replace `https://github.com/Akash1912-hub/IIT-KANPUR-PROJECT/main/traffic_light.git` with the actual URL of your GitHub repository.
- Ensure that you include any necessary files (such as `requirements.txt` and the dataset) in your repository for a complete setup.

Let me know if you need any further changes to the `README.md` or other parts of the project!
