# Simulation Usage
This repository contains files and scripts for simulating an arm using CoppeliaSim.

## Getting Started
1. **Download CoppeliaSim Education**: Download and install CoppeliaSim Education from [here](https://www.coppeliarobotics.com).

2. **Installation**: Install the required Python package for communication with CoppeliaSim:
    ```bash
    pip install coppeliasim-zmqremoteapi-client
    ```

3. **File Contents**:
    - `armSIM(3dof).ttt`: CoppeliaSim simulation file.
    - `clawArmSim(3DoF)`: CoppeliaSim simulation file with our custom claw.
    - `kinematics.m`: MATLAB script for kinematics calculations.

## Usage

1. **Start CoppeliaSim**: Launch CoppeliaSim and open the `armSIM(3dof).ttt` simulation file.

2. **Run Python Script**: Execute the `main.py` Python script in the root folder (up one from here). This script communicates with CoppeliaSim and controls the arm simulation.

3. **Watch the Simulation**: Observe the arm movement in the CoppeliaSim environment as controlled by the Python script.

## Notes

- Always remember to pull the latest changes from the repository before pushing any modifications.
