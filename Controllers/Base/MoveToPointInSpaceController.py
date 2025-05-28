import math
import logging
import numpy as np
import sympy as sym
import time

from Config.ArmPhysicalParameters import ArmPhysicalParameters
from HALs.HAL_base import HAL_base
from Controllers.Base.Controller import Controller

# --- Constants for Magic Numbers ---
SMOOTHING_FACTOR = 0.1
ANGLE_OFFSET_90 = 90
ANGLE_OFFSET_180 = 180
FRAME_SLEEP_SECONDS = 0.03
HARD_CODED_ANGLE_RAD = math.radians(22.5)
A6_EPSILON = 0.0001
M_TO_CM = 100
PIXEL_TO_METER = 0.01
resize_fx = 0.25
resize_fy = 0.25

# Utility functions - - - - - - - - - -
def set_arm_target_position(
    x: float,
    y: float,
    z: float,
    hal: 'HAL_base',
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float = 0.1
) -> bool:
    """
    Calculates and commands the arm to reach the given (x, y, z) position.

    Args:
        x (float): Target x coordinate.
        y (float): Target y coordinate.
        z (float): Target z coordinate.
        hal: Hardware abstraction layer for controlling the arm.
        arm_params (ArmPhysicalParameters): Arm physical parameters (required).
        smoothing_factor (float): Smoothing factor for joint movement.

    Returns:
        bool: True if the position is reachable and command sent, False if fallback was used.

    Raises:
        ValueError: If arm_params is not provided.
        Exception: For unexpected errors.
    """

    try:
        angles = _calculate_kinematics(x, y, z, arm_params)
        if angles is None:
            logging.warning("Target position unreachable, using fallback kinematics.")
            _fallback_kinematics(x, y, z, hal, arm_params, smoothing_factor)
            return False
        else:
            _command_hardware(angles, x, y, z, hal, arm_params, smoothing_factor)
            return True
    except Exception as err:
        logging.exception(f"Exception in set_arm_target_position: {err}")
        raise

def _calculate_kinematics(
    x: float,
    y: float,
    z: float,
    arm_params: 'ArmPhysicalParameters'
) -> 'tuple[float, float, float] | None':
    """
    Calculates joint angles using the arm's kinematics.

    Returns:
        tuple or None: (theta1_deg, theta2_deg, theta3_deg) if reachable, else None.
    """
    robot_arm = Three_Degree_Arm(
        arm_params.a1, arm_params.a2, arm_params.a3,
        arm_params.a4, arm_params.a5, arm_params.a6
    )
    return robot_arm.calculate_angles(sym.Matrix([x, y, z, 1]))

def _fallback_kinematics(
    x: float,
    y: float,
    z: float,
    hal: 'HAL_base',
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float
) -> None:
    """
    Fallback for unreachable positions: computes simple base and shoulder angles.
    """
    a1 = arm_params.a1
    ANGLE_OFFSET_90 = 90
    ANGLE_OFFSET_180 = 180

    theta = sym.atan2(y, x) if (x != 0 or y != 0) else 0
    opp = z - a1
    dist = sym.sqrt(x ** 2 + y ** 2)
    t0deg = float(sym.deg(theta).evalf()) + ANGLE_OFFSET_180
    t0deg = (t0deg + 360) % 360
    theta1 = sym.atan(opp / dist) if dist != 0 else ANGLE_OFFSET_90
    t1deg = ANGLE_OFFSET_90 - (float(sym.deg(theta1).evalf()))
    t0n = hal.get_joint(0)
    t1n = hal.get_joint(1)
    t0n = t0n + (t0deg - t0n) * smoothing_factor
    t1n = t1n + (t1deg - t1n) * smoothing_factor
    hal.set_joint(0, t0n)
    hal.set_joint(1, t1n)
    hal.set_joint(2, 0)
    logging.info(f"Fallback kinematics used: base={t0n:.2f}, shoulder={t1n:.2f}, elbow=0")

def _command_hardware(
    angles: tuple[float, float, float],
    x: float,
    y: float,
    z: float,
    hal: 'HAL_base',
    arm_params: ArmPhysicalParameters,
    smoothing_factor: float
) -> None:
    """
    Sends calculated joint angles to the hardware, with optional smoothing.
    """
    ANGLE_OFFSET_90 = 90
    ANGLE_OFFSET_180 = 180

    theta = sym.atan2(y, x) if (x != 0 or y != 0) else 0
    t0deg = float(sym.deg(theta).evalf()) + ANGLE_OFFSET_180
    t0deg = (t0deg + 360) % 360
    angle_base = t0deg
    angle_base = (angle_base + 360) % 360
    angle_1 = -(angles[1] - ANGLE_OFFSET_90)
    angle_2 = -(angles[2] - ANGLE_OFFSET_90)

    # Always use smoothing for consistency
    base_val = hal.get_joint(0) + smoothing_factor * (angle_base - hal.get_joint(0))
    shoulder_val = hal.get_joint(1) + smoothing_factor * (angle_1 - hal.get_joint(1))
    elbow_val = hal.get_joint(2) + smoothing_factor * (angle_2 - hal.get_joint(2))
    hal.set_joint(0, base_val)
    hal.set_joint(1, shoulder_val)
    hal.set_joint(2, elbow_val)
    logging.info(f"Smooth move: base={base_val:.2f}, shoulder={shoulder_val:.2f}, elbow={elbow_val:.2f}")

class Three_Degree_Arm:
    def __init__(self, a1: float, a2: float, a3: float, a4: float, a5: float, a6: float) -> None:
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a4 = a4
        self.a5 = a5
        self.a6 = a6

    def DH_matrix(self, theta: float, alpha: float, r: float, d: float) -> sym.Matrix:
        return sym.Matrix([
            [sym.cos(theta), -sym.sin(theta) * sym.cos(alpha), sym.sin(theta) * sym.sin(alpha), r * sym.cos(theta)],
            [sym.sin(theta), sym.cos(theta) * sym.cos(alpha), -sym.cos(theta) * sym.sin(alpha), r * sym.sin(theta)],
            [0, sym.sin(alpha), sym.cos(alpha), d],
            [0, 0, 0, 1]
        ])

    def calculate_angles(self, EE: sym.Matrix) -> 'tuple[float, float, float] | None':
        x, y, z = EE[0], EE[1], EE[2]

        # Condition checks
        cond1 = (np.abs(x) - self.a3) ** 2 + (z - self.a1) ** 2 < (self.a5 + self.a6) ** 2 and np.abs(
            x) > self.a3 and 0 < z < self.a1
        cond2 = np.abs(x) ** 2 + (z - self.a1) ** 2 < (self.a3 + self.a5 + self.a6) ** 2 and np.abs(x) ** 2 + (
                z - self.a1) ** 2 > self.a3 ** 2 and np.abs(x) > 0 and z > self.a1

        isInRegion = cond1 or cond2

        if isInRegion:
            print('The point is inside the region.')
            print(EE)
            theta1 = sym.atan2(y, x)

            H0_1 = self.DH_matrix(theta1, sym.pi / 2, 0, self.a1)
            EE_local_H0_1 = H0_1.inv() * EE

            EE_x_H0_1 = EE_local_H0_1[0]
            # not used in this context
            # EE_y_H0_1 = EE_local_H0_1[2]
            EE_z_H0_1 = EE_local_H0_1[1]

            l1 = self.a3
            l2 = self.a5 + self.a6
            R = sym.sqrt(EE_x_H0_1 ** 2 + EE_z_H0_1 ** 2)
            theta = sym.atan(EE_z_H0_1 / EE_x_H0_1)

            beta = sym.acos((R ** 2 - l1 ** 2 - l2 ** 2) / (-2 * l1 * l2))
            if not beta.is_real:
                return None
            alpha = sym.asin((l2 * sym.sin(beta)) / R)
            print(alpha)
            theta2 = theta + alpha
            theta3 = beta - sym.pi / 2

            theta4 = 0

            print(theta2.evalf())
            print(theta3.evalf())

            H1_2 = self.DH_matrix(theta2, 0, self.a3, -self.a2)
            H2_3 = self.DH_matrix(theta3, sym.pi / 2, 0, self.a4)
            H3_4 = self.DH_matrix(theta4, 0, 0, self.a5 + self.a6)

            H0_2 = H0_1 * H1_2
            H0_3 = H0_2 * H2_3
            H0_4 = H0_3 * H3_4

            EE_position = H0_4[:3, 3]
            print('EE Position (CM):')
            # print(f'x: {float(EE_position[0].evalf()):.2f}')
            # print(f'y: {float(EE_position[1].evalf()):.2f}')
            # print(f'z: {float(EE_position[2].evalf()):.2f}')

            theta1_deg = sym.deg(theta1.evalf())
            theta2_deg = sym.deg(theta2.evalf())
            theta3_deg = sym.deg(theta3.evalf())

            print('\nTheta Angles:')
            print(f'Base: {theta1_deg.evalf():.2f} degrees')
            print(f'1: {theta2_deg.evalf():.2f} degrees')
            print(f'2: {theta3_deg.evalf():.2f} degrees')
            return theta1_deg, theta2_deg, theta3_deg
        else:
            print('This point is not feasible')
        return None
    
# End Utility functions - - - - - - - - - -

class MoveToPointInSpaceController(Controller):

    def __init__(self, selected_HAL: HAL_base, arm_params: ArmPhysicalParameters) -> None:
        Controller.__init__(selected_HAL)
        self.selected_HAL: HAL_base = selected_HAL
        self.arm_params: ArmPhysicalParameters = arm_params
        
    def start(self) -> None:
        # Initialize current position (could also read from hardware)
        joint_positions = self.get_joint_positions()[-1]  # End effector position
        self.current_x = joint_positions[0]
        self.current_y = joint_positions[1]
        self.current_z = joint_positions[2]
        self.target_cord_x = 0
        self.target_cord_y = 0
        self.target_cord_z = 0
        
        self.target_diameter_pixels = 0
        
        self.keep_running = True

    def stop(self) -> None:
        self.keep_running = False

    def set_target_position_in_space(self, x: int, y: int, z: int, target_diameter_pixels: int) -> None:
        """
        Set the target position in space for the arm to move to.
        :param x: Target cordinate in the x direction.
        :param y: Target cordinate in the y direction.
        :param z: Target cordinate in the z direction.
        :param target_diameter_pixels: Diameter of the target in pixels.
        """
        self.target_cord_x = x
        self.target_cord_y = y
        self.target_cord_z = z
        
        self.target_diameter_pixels = target_diameter_pixels
        
        set_arm_target_position(
            x / M_TO_CM,  # Convert cm to m
            y / M_TO_CM,  # Convert cm to m
            z / M_TO_CM,  # Convert cm to m
            self.selected_HAL,
            self.arm_params,
            smoothing_factor=SMOOTHING_FACTOR
        )

    def step_towards_target(self, step_size: float = 1.0) -> None:
        # Move a small step towards the target
        dx = self.target_cord_x - self.current_x
        dy = self.target_cord_y - self.current_y
        dz = self.target_cord_z - self.current_z

        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        if distance < step_size:
            # Close enough, set to target
            self.current_x = self.target_cord_x
            self.current_y = self.target_cord_y
            self.current_z = self.target_cord_z
        else:
            # Step towards target
            self.current_x += dx / distance * step_size
            self.current_y += dy / distance * step_size
            self.current_z += dz / distance * step_size

        set_arm_target_position(
            self.current_x / M_TO_CM,
            self.current_y / M_TO_CM,
            self.current_z / M_TO_CM,
            self.selected_HAL,
            self.arm_params,
            smoothing_factor=SMOOTHING_FACTOR
        )

    def run_to_target(self, step_size: float = 1.0, interval: float = 0.03) -> None:
        self.keep_running = True
        while self.keep_running:
            self.step_towards_target(step_size)
            # Stop if at target
            if (self.current_x == self.target_cord_x and
                self.current_y == self.target_cord_y and
                self.current_z == self.target_cord_z):
                break
            time.sleep(interval)

    def test_move(self, step_size: float = 2.0, interval: float = 0.05) -> None:
        """
        Move the arm to the furthest extents in each axis in a loop.
        Prints 'Success' when each point is reached.
        Uses ArmPhysicalParameters to calculate the workspace.
        """
        # Calculate reach in the X-Y plane (ignoring offsets for simplicity)
        max_reach = self.arm_params.a3 + self.arm_params.a5 + self.arm_params.a6
        min_reach = self.arm_params.a2  # horizontal offset from shoulder to elbow

        # Z extents
        z_min = self.arm_params.a1  # base height
        z_max = self.arm_params.a1 + self.arm_params.a3 + self.arm_params.a5 + self.arm_params.a6

        # Four extreme points (in centimeters)
        points = [
            (max_reach, 0, z_min),           # Far right, lowest
            (0, max_reach, z_min),           # Far forward, lowest
            (max_reach, 0, z_max),           # Far right, highest
            (0, max_reach, z_max),           # Far forward, highest
        ]

        for idx, (x, y, z) in enumerate(points):
            print(f"Moving to point {idx+1}: ({x:.2f}, {y:.2f}, {z:.2f})")
            self.set_target_position_in_space(x, y, z, target_diameter_pixels=0)
            joint_positions = self.get_joint_positions()[-1]
            self.current_x = joint_positions[0]
            self.current_y = joint_positions[1]
            self.current_z = joint_positions[2]
            while (abs(self.current_x - x) > 1 or
                   abs(self.current_y - y) > 1 or
                   abs(self.current_z - z) > 1):
                self.step_towards_target(step_size)
                time.sleep(interval)
            print(f"Success: Reached point {idx+1} ({x:.2f}, {y:.2f}, {z:.2f})")

    def get_joint_angles(self) -> list[float]:
        """Return a list of current joint angles in degrees."""
        return [self.selected_HAL.get_joint(i) for i in range(self.selected_HAL.joint_count())]

    def get_joint_positions(self) -> list[tuple[float, float, float]]:
        """
        Return a list of (x, y, z) positions for each joint, including the end effector.
        Uses DH parameters from ArmPhysicalParameters.
        """
        # Get current joint angles in radians
        thetas = [math.radians(self.selected_HAL.get_joint(i)) for i in range(self.selected_HAL.joint_count())]
        # Get DH parameters
        a1 = self.arm_params.a1
        a2 = self.arm_params.a2
        a3 = self.arm_params.a3
        a4 = self.arm_params.a4
        a5 = self.arm_params.a5
        a6 = self.arm_params.a6

        # Build DH table: (theta, alpha, r, d)
        dh_params = [
            (thetas[0], math.pi/2, 0, a1),
            (thetas[1], 0, a3, -a2),
            (thetas[2], math.pi/2, 0, a4),
            (0, 0, 0, a5 + a6)
        ]

        # Start with identity matrix
        T = np.eye(4)
        positions = [(0, 0, 0)]  # Base at origin

        for theta, alpha, r, d in dh_params:
            T = np.dot(T, self._dh_matrix(theta, alpha, r, d))
            pos = T[:3, 3]
            positions.append(tuple(float(x) for x in pos))

        return positions  # Each is (x, y, z), last is end effector

    def get_end_effector_position(self) -> tuple[float, float, float]:
        """Return the (x, y, z) position of the end effector."""
        return self.get_joint_positions()[-1]
    
    def get_end_effector_rotation(self) -> tuple[float, float, float]:
        """
        Return the current forward direction (z-axis) of the end effector as a 3-tuple.
        """
        # Get current joint angles in radians
        thetas = [math.radians(self.selected_HAL.get_joint(i)) for i in range(self.selected_HAL.joint_count())]
        a1 = self.arm_params.a1
        a2 = self.arm_params.a2
        a3 = self.arm_params.a3
        a4 = self.arm_params.a4
        a5 = self.arm_params.a5
        a6 = self.arm_params.a6

        dh_params = [
            (thetas[0], math.pi/2, 0, a1),
            (thetas[1], 0, a3, -a2),
            (thetas[2], math.pi/2, 0, a4),
            (0, 0, 0, a5 + a6)
        ]

        T = np.eye(4)
        for theta, alpha, r, d in dh_params:
            T = np.dot(T, self._dh_matrix(theta, alpha, r, d))
        # The forward direction is the z-axis of the end effector frame (third column of rotation part)
        forward = T[:3, 2]
        return tuple(float(x) for x in forward)

    @staticmethod
    def _dh_matrix(theta: float, alpha: float, r: float, d: float) -> np.ndarray:
        """Return the DH transformation matrix."""
        return np.array([
            [np.cos(theta), -np.sin(theta)*np.cos(alpha),  np.sin(theta)*np.sin(alpha), r*np.cos(theta)],
            [np.sin(theta),  np.cos(theta)*np.cos(alpha), -np.cos(theta)*np.sin(alpha), r*np.sin(theta)],
            [0,              np.sin(alpha),                np.cos(alpha),               d],
            [0,              0,                            0,                           1]
        ])

