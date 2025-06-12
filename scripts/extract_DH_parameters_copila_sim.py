"""
Script to calculate and print Denavit-Hartenberg (DH) parameters
from a CoppeliaSim scene using the ZeroMQ Remote API.

This script assumes the arm's joint hierarchy matches the provided screenshot.
"""

from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import numpy as np

def get_transform(sim, child, parent):
    """Get the transformation matrix from parent to child."""
    pos = sim.getObjectPosition(child, parent)
    quat = sim.getObjectQuaternion(child, parent)
    # Convert quaternion [x, y, z, w] to rotation matrix
    x, y, z, w = quat
    rot = np.array([
        [1 - 2*(y**2 + z**2),     2*(x*y - z*w),     2*(x*z + y*w)],
        [    2*(x*y + z*w), 1 - 2*(x**2 + z**2),     2*(y*z - x*w)],
        [    2*(x*z - y*w),     2*(y*z + x*w), 1 - 2*(x**2 + y**2)]
    ])
    T = np.eye(4)
    T[:3,:3] = rot
    T[:3,3] = pos
    return T

def dh_from_transform(T):
    """
    Extract DH parameters (a, alpha, d, theta) from a homogeneous transform.
    This is a simplified version and assumes standard DH conventions.
    """
    a = np.linalg.norm(T[0:3,3])
    alpha = np.arctan2(T[2,1], T[2,2])
    d = T[2,3]
    theta = np.arctan2(T[1,0], T[0,0])
    return a, np.degrees(alpha), d, np.degrees(theta)

def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    # List of joint paths in order (from base to end-effector)
    joint_paths = [
        '/Base/BaseRevolute',
        '/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute',
        '/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute',
        '/Base/BaseRevolute/LowerSmallerLimb/Limb1Revolute/BigLimb/Limb2Revolute/UpperSmallLimb/Limb4Revolute'
    ]

    # Get handles for each joint
    joint_handles = [sim.getObjectHandle(path) for path in joint_paths]

    print("DH Parameters (a [m], alpha [deg], d [m], theta [deg]):")
    dh_params = []
    for i in range(len(joint_handles)-1):
        parent = joint_handles[i]
        child = joint_handles[i+1]
        T = get_transform(sim, child, parent)
        a, alpha, d, theta = dh_from_transform(T)
        dh_params.append((a, alpha, d, theta))
        print(f"Joint {i+1}: a={a:.4f} m, alpha={alpha:.2f}°, d={d:.4f} m, theta={theta:.2f}°")

    # Map extracted DH a values to a1-a6 (fill with 0 if not enough joints)
    a_values = [a for a, _, _, _ in dh_params]
    while len(a_values) < 6:
        a_values.append(0.0)

    print("\n# --- ArmPhysicalParameters (extracted from simulation) ---")
    print("class ArmPhysicalParameters:")
    print("    \"\"\"Extracted from CoppeliaSim scene.\"\"\"")
    print(f"    a1: float = {a_values[0]*100:.2f}   # [cm] Height from base to shoulder joint")
    print(f"    a2: float = {a_values[1]*100:.2f}   # [cm] Horizontal offset from shoulder to elbow")
    print(f"    a3: float = {a_values[2]*100:.2f}   # [cm] Length of upper arm (shoulder to elbow)")
    print(f"    a4: float = {a_values[3]*100:.2f}   # [cm] Horizontal offset from elbow to wrist")
    print(f"    a5: float = {a_values[4]*100:.2f}   # [cm] Length of forearm (elbow to wrist)")
    print(f"    a6: float = {a_values[5]*100:.2f}   # [cm] Length from wrist to end-effector (gripper/tool)")
    print("    # ...other parameters as needed...")

if __name__ == "__main__":
    main()