"""
Stereo Rotation (Debug Mode)
Applies simple stereo panning based on yaw angle
"""

import numpy as np


class StereoRotator:
    """Simple stereo rotation using amplitude panning"""

    def __init__(self):
        """Initialize the stereo rotator"""
        pass

    def rotate(self, stereo_frame, yaw_degrees):
        """
        Rotate stereo audio by applying amplitude panning

        When you turn your head right (+yaw), sound should shift left

        Args:
            stereo_frame: numpy array of shape (num_samples, 2) - stereo audio
            yaw_degrees: head rotation in degrees (positive = clockwise)

        Returns:
            numpy array of shape (num_samples, 2) - rotated stereo audio
        """
        num_samples = stereo_frame.shape[0]
        left = stereo_frame[:, 0]
        right = stereo_frame[:, 1]

        # Normalize yaw to -180 to +180
        yaw = yaw_degrees % 360
        if yaw > 180:
            yaw -= 360

        # STEREO LIMITATION: We can only represent front hemisphere properly
        # For rear sounds, we mirror them back to front and reduce volume

        abs_yaw = abs(yaw)

        # Calculate volume reduction for rear sounds
        if abs_yaw > 90:
            # Sound is behind us - reduce volume
            # At 90°: 100% volume
            # At 180°: 20% volume (almost silent)
            rear_factor = (abs_yaw - 90) / 90  # 0 to 1
            volume = 1.0 - (rear_factor * 0.8)

            # Mirror rear sounds to front
            # 180° -> 0° (center)
            # 135° -> 45° (angled front)
            # 90° -> 90° (side)
            mirrored_yaw = 180 - abs_yaw
            # Preserve the sign (left/right)
            if yaw < 0:
                pan_yaw = -mirrored_yaw
            else:
                pan_yaw = mirrored_yaw
        else:
            # Sound is in front - full volume, normal position
            volume = 1.0
            pan_yaw = yaw

        # Calculate pan position (-1 = full left, 0 = center, +1 = full right)
        # When head turns right (+yaw), sound should pan left (negative)
        pan = -pan_yaw / 90.0  # Maps -90..+90 to +1..-1
        pan = max(-1.0, min(1.0, pan))  # Clamp to valid range

        # Constant power panning (equal power law)
        pan_radians = pan * np.pi / 4  # Maps -1..+1 to -π/4..+π/4

        left_gain = np.cos(pan_radians - np.pi/4) * volume
        right_gain = np.cos(pan_radians + np.pi/4) * volume

        # Mix input channels with panning gains
        output = np.zeros((num_samples, 2), dtype=np.float32)

        # Create a mono mix, then pan it
        mono = (left + right) * 0.5

        output[:, 0] = mono * left_gain   # Left output
        output[:, 1] = mono * right_gain  # Right output

        return output


if __name__ == "__main__":
    # Test the stereo rotator
    import matplotlib.pyplot as plt

    rotator = StereoRotator()

    # Generate test tone
    duration = 1.0
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)

    # Mono test signal
    mono_signal = np.sin(2 * np.pi * 440 * t) * 0.3
    stereo = np.column_stack([mono_signal, mono_signal])

    # Test at different angles
    test_angles = [-90, -45, 0, 45, 90, 135, 180]

    print("Stereo Rotation Test")
    print("=" * 50)

    for angle in test_angles:
        rotated = rotator.rotate(stereo, angle)

        left_rms = np.sqrt(np.mean(rotated[:, 0] ** 2))
        right_rms = np.sqrt(np.mean(rotated[:, 1] ** 2))

        left_db = 20 * np.log10(left_rms + 1e-10)
        right_db = 20 * np.log10(right_rms + 1e-10)

        print(f"\nYaw: {angle:4d}°")
        print(f"  Left:  {left_db:6.1f} dB")
        print(f"  Right: {right_db:6.1f} dB")

    print("\n" + "=" * 50)
    print("Expected:")
    print("  -90° (facing left): Left loud, Right quiet")
    print("    0° (forward):     Left and Right equal")
    print("  +90° (facing right): Left quiet, Right loud")
