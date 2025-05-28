class ArmPhysicalParameters:
    """
    Holds all physical and calibration parameters for the robotic arm.
    Modify these values to match your specific hardware setup.
    """

    # --- Denavit-Hartenberg (DH) Parameters ---
    # These define the geometry of the arm for kinematics calculations.
    a1: float = 13.1   # [cm] Height from base to shoulder joint
    a2: float = 3.25   # [cm] Horizontal offset from shoulder to elbow
    a3: float = 11.4   # [cm] Length of upper arm (shoulder to elbow)
    a4: float = 3.25   # [cm] Horizontal offset from elbow to wrist
    a5: float = 5.8    # [cm] Length of forearm (elbow to wrist)
    a6: float = 11.11  # [cm] Length from wrist to end-effector (gripper/tool)

    # --- Joint Limits ---
    # Set the minimum and maximum allowed angles for each joint (in degrees).
    base_min: float = 0      # Minimum base rotation
    base_max: float = 270    # Maximum base rotation
    joint1_min: float = 0    # Minimum angle for joint 1
    joint1_max: float = 90   # Maximum angle for joint 1
    joint2_min: float = 0    # Minimum angle for joint 2
    joint2_max: float = 75   # Maximum angle for joint 2

    # --- Camera Calibration Parameters ---
    # These are used for vision-based distance and position estimation.
    sensor_size: float = 0.006      # [m] Physical width of camera sensor
    focal_length: float = 0.0063    # [m] Focal length of camera lens
    sensor_res: int = 1257          # [pixels] Horizontal resolution of camera sensor
    fov: float = 60                 # [degrees] Field of view of the camera

    # --- Offsets for Kinematic Calculations ---
    kinematic_offset_y: float = 52.454 / 1000  # [m] Y offset for end-effector calibration
    kinematic_offset_z: float = 33.704 / 1000  # [m] Z offset for end-effector calibration
    

    # --- Notes for Modification ---
    # - Always measure your arm's physical dimensions carefully and update the DH parameters.
    # - If you change the camera or lens, update the camera calibration parameters.
    # - Tune control parameters (K, lambda_, error_tolerance_coord) for smooth and accurate movement.
    # - Adjust joint limits to match your hardware's safe operating range.
    # - Offsets should be measured/calibrated for your specific end-effector/tool.
    # - If you change image resolution or processing, update the vision parameters accordingly.

    # Example usage:
    # from Config.ArmPhysicalParameters import ArmPhysicalParameters
    # params = ArmPhysicalParameters()
    # print(params.a1)