# Simulation Usage
This repository contains files and scripts for simulating an arm using CoppeliaSim.

## Getting Started
1. **Download CoppeliaSim Education**: Download and install CoppeliaSim Education from [here](https://www.coppeliarobotics.com).

2. **Installation**: Install the required Python package for communication with CoppeliaSim:
    ```bash
    pip install coppeliasim-zmqremoteapi-client
    ```

3. **File Contents**:
    - `armSIM.ttt`: CoppeliaSim simulation file.
    - `ARM_SIM.py`: Python script for remote API communication with the CoppeliaSim simulation file.
    - `kinematicsPYV1.py`: Python script for kinematics calculations.
    - `kinematics.m`: MATLAB script for kinematics calculations.

## Usage

1. **Start CoppeliaSim**: Launch CoppeliaSim and open the `armSIM.ttt` simulation file.

2. **Run Python Script**: Execute the `ARM_SIM.py` Python script. This script communicates with CoppeliaSim and controls the arm simulation.

3. **Watch the Simulation**: Observe the arm movement in the CoppeliaSim environment as controlled by the Python script.

## Notes

- Always remember to pull the latest changes from the repository before pushing any modifications.
