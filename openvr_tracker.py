"""
OpenVR Tracker for VR headset yaw tracking
Captures SteamVR headset yaw directly from OpenVR
"""

import openvr
import threading
import time
import math


def matrix_to_yaw(mat):
    """
    Extract yaw angle directly from rotation matrix

    Args:
        mat: 3x4 transformation matrix from OpenVR

    Returns:
        Yaw angle in degrees (0-360 range)
    """
    # Extract yaw from rotation matrix
    # For OpenVR coordinate system (Y-up, right-handed):
    # Yaw is rotation around Y axis
    # We use atan2 of the forward vector's X and Z components

    # Forward vector is the Z column (index 2) of rotation matrix
    # In OpenVR, looking forward is -Z
    forward_x = mat[0][2]
    forward_z = mat[2][2]

    # Calculate yaw angle
    yaw_rad = math.atan2(forward_x, forward_z)
    yaw_deg = math.degrees(yaw_rad)

    # Invert direction (negate) so turning right gives positive values
    yaw_deg = -yaw_deg

    # Normalize to 0-360 range
    yaw_deg = yaw_deg % 360

    return yaw_deg


class OpenVRTracker:
    """Tracks VR headset yaw rotation using OpenVR"""

    def __init__(self):
        self.yaw = 0.0  # Current yaw angle in degrees
        self.vr_system = None
        self.tracking_thread = None
        self.running = False

    def start(self):
        """Start OpenVR tracking in a background thread"""
        # Initialize OpenVR
        try:
            self.vr_system = openvr.init(openvr.VRApplication_Background)
            print("✓ OpenVR initialized")
        except Exception as e:
            print(f"✗ Failed to initialize OpenVR: {e}")
            print("\nMake sure:")
            print("  1. SteamVR is running")
            print("  2. Your VR headset is connected")
            raise

        # Start tracking thread
        self.running = True
        self.tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True
        )
        self.tracking_thread.start()
        print("✓ OpenVR tracking started")

    def stop(self):
        """Stop OpenVR tracking"""
        self.running = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
        if self.vr_system:
            openvr.shutdown()
            print("OpenVR shut down")

    def get_yaw(self):
        """Get current yaw angle in degrees"""
        return self.yaw

    def _tracking_loop(self):
        """Background thread that continuously reads headset yaw"""
        while self.running:
            try:
                # Get poses for all devices
                poses = self.vr_system.getDeviceToAbsoluteTrackingPose(
                    openvr.TrackingUniverseStanding,
                    0,
                    openvr.k_unMaxTrackedDeviceCount
                )

                # Find HMD (device index 0 is always the headset)
                hmd_index = openvr.k_unTrackedDeviceIndex_Hmd
                pose = poses[hmd_index]

                if pose.bPoseIsValid:
                    # Extract rotation matrix
                    mat = pose.mDeviceToAbsoluteTracking

                    # Extract yaw directly from matrix
                    self.yaw = matrix_to_yaw(mat)

            except Exception as e:
                print(f"OpenVR tracking error: {e}")
                time.sleep(0.1)
                continue

            # Update at ~60 Hz
            time.sleep(1.0 / 60.0)


class TestTracker:
    """Test tracker for simulating head movement without VR hardware"""

    def __init__(self, mode="static"):
        """
        Initialize test tracker

        Args:
            mode: "rotate", "sweep", or "static"
        """
        self.mode = mode
        self.yaw = 0.0
        self.time = 0.0
        self.running = False
        self.tracking_thread = None

    def start(self):
        """Start test tracking"""
        self.running = True

        if self.mode == "static":
            print("✓ Static test mode - yaw will remain at 0° (modify in real-time if needed)")
        else:
            self.tracking_thread = threading.Thread(
                target=self._tracking_loop,
                daemon=True
            )
            self.tracking_thread.start()
            print(f"✓ Test tracking started ({self.mode} mode)")

    def stop(self):
        """Stop test tracking"""
        self.running = False
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)

    def get_yaw(self):
        """Get current yaw angle in degrees"""
        return self.yaw

    def set_yaw(self, yaw_degrees):
        """Set yaw angle manually (for static mode)"""
        self.yaw = float(yaw_degrees)

    def _tracking_loop(self):
        """Background thread that generates test patterns"""
        while self.running:
            if self.mode == "rotate":
                # Continuous rotation: 30 degrees per second
                self.yaw = (self.time * 30) % 360

            elif self.mode == "sweep":
                # Sweep back and forth: -180 to +180
                self.yaw = math.sin(self.time * 0.5) * 180

            self.time += 0.02  # 50 Hz update rate
            time.sleep(0.02)


if __name__ == "__main__":
    # Test the tracker
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        print("Testing TestTracker in rotate mode...")
        tracker = TestTracker(mode="rotate")
        tracker.start()

        try:
            for _ in range(50):  # 1 second
                print(f"\rYaw: {tracker.get_yaw():6.1f}°", end="", flush=True)
                time.sleep(0.02)
            print("\n✓ Test successful")
        finally:
            tracker.stop()

    else:
        # OpenVR mode
        print("Testing OpenVRTracker...")
        print("Make sure SteamVR is running!\n")

        tracker = OpenVRTracker()
        tracker.start()

        try:
            print("Tracking headset - Press Ctrl+C to stop\n")
            while True:
                print(f"\rYaw: {tracker.get_yaw():7.2f}°", end="", flush=True)
                time.sleep(0.05)
        except KeyboardInterrupt:
            print("\n\nStopping...")
        finally:
            tracker.stop()
