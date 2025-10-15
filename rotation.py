"""
Surround Sound Rotation Engine
Rotates 5.1 or 7.1 soundfield around the yaw axis based on head tracking
"""

import numpy as np


class SurroundRotator:
    """Rotates 5.1 or 7.1 surround soundfield based on yaw angle"""

    # Speaker positions for different formats
    # ITU-R BS.775-3 standard positions (0° = front, positive = clockwise)
    SPEAKER_ANGLES_71 = {
        0: 30,      # L (Front Left)
        1: -30,     # R (Front Right)
        2: 0,       # C (Center)
        3: 0,       # LFE (Subwoofer - non-directional)
        4: 110,     # LS (Left Surround)
        5: -110,    # RS (Right Surround)
        6: 150,     # LB (Left Back)
        7: -150,    # RB (Right Back)
    }

    SPEAKER_ANGLES_51 = {
        0: 30,      # L (Front Left)
        1: -30,     # R (Front Right)
        2: 0,       # C (Center)
        3: 0,       # LFE (Subwoofer - non-directional)
        4: 110,     # LS (Left Surround)
        5: -110,    # RS (Right Surround)
    }

    def __init__(self, format="7.1"):
        """
        Initialize the rotation engine

        Args:
            format: "5.1" or "7.1" surround format
        """
        self.format = format
        self.num_channels = 6 if format == "5.1" else 8
        self.SPEAKER_ANGLES = self.SPEAKER_ANGLES_51 if format == "5.1" else self.SPEAKER_ANGLES_71

    def rotate(self, surround_frame, yaw_degrees):
        """
        Rotate the surround soundfield by the given yaw angle

        Args:
            surround_frame: numpy array of shape (num_samples, 6 or 8) - surround audio
            yaw_degrees: head rotation in degrees (positive = clockwise)

        Returns:
            numpy array of shape (num_samples, 6 or 8) - rotated surround audio
        """
        num_samples = surround_frame.shape[0]
        output = np.zeros((num_samples, self.num_channels), dtype=np.float32)

        # For each output speaker, determine which input channels contribute
        for out_channel in range(self.num_channels):
            out_angle = self.SPEAKER_ANGLES[out_channel]

            # LFE is non-directional, just pass through
            if out_channel == 3:
                output[:, out_channel] = surround_frame[:, 3]
                continue

            # Calculate the rotated position this output speaker should receive
            # Add yaw to rotate the soundfield (head turns right, sound appears to rotate left)
            rotated_angle = (out_angle + yaw_degrees) % 360
            if rotated_angle > 180:
                rotated_angle -= 360

            # Use amplitude panning to blend between adjacent input channels
            blended_signal = self._amplitude_pan(surround_frame, rotated_angle)
            output[:, out_channel] = blended_signal

        return output

    def _amplitude_pan(self, surround_frame, target_angle):
        """
        Use amplitude panning to blend between speakers at target angle

        Args:
            surround_frame: input 7.1 audio frame
            target_angle: angle in degrees where we want to place the sound

        Returns:
            blended audio signal for this position
        """
        # Find the two closest speakers to the target angle
        # Exclude LFE (channel 3) from spatial calculations
        spatial_channels = [i for i in range(self.num_channels) if i != 3]

        closest_channels = sorted(
            spatial_channels,
            key=lambda ch: self._angle_distance(
                self.SPEAKER_ANGLES[ch], target_angle
            )
        )[:2]

        if len(closest_channels) == 0:
            return np.zeros(surround_frame.shape[0], dtype=np.float32)

        if len(closest_channels) == 1:
            return surround_frame[:, closest_channels[0]]

        # Get the two closest channels
        ch1, ch2 = closest_channels[0], closest_channels[1]
        angle1 = self.SPEAKER_ANGLES[ch1]
        angle2 = self.SPEAKER_ANGLES[ch2]

        # Calculate pan weights using constant power panning
        dist1 = self._angle_distance(angle1, target_angle)
        dist2 = self._angle_distance(angle2, target_angle)

        # Avoid division by zero
        total_dist = dist1 + dist2
        if total_dist < 0.1:
            weight1 = 1.0
            weight2 = 0.0
        else:
            # Inverse distance weighting with constant power
            weight2 = dist1 / total_dist
            weight1 = dist2 / total_dist

            # Apply constant power panning (equal power, not equal amplitude)
            # Convert to radians for sine/cosine
            angle_rad = weight2 * np.pi / 2
            weight1 = np.cos(angle_rad)
            weight2 = np.sin(angle_rad)

        # Blend the two channels
        blended = (
            surround_frame[:, ch1] * weight1 +
            surround_frame[:, ch2] * weight2
        )

        return blended

    def _angle_distance(self, angle1, angle2):
        """
        Calculate the shortest angular distance between two angles

        Args:
            angle1, angle2: angles in degrees

        Returns:
            shortest distance in degrees (0-180)
        """
        diff = abs(angle1 - angle2) % 360
        if diff > 180:
            diff = 360 - diff
        return diff


if __name__ == "__main__":
    # Test rotation
    rotator = SurroundRotator()

    # Create test signal with sound at front left (30°)
    num_samples = 1000
    test_frame = np.zeros((num_samples, 8), dtype=np.float32)
    test_frame[:, 0] = 1.0  # Sound in front left speaker

    print("Original signal: Front Left channel = 1.0")
    print(f"Channel levels: {test_frame[0, :]}")

    # Rotate by 30° clockwise (should move to center)
    rotated = rotator.rotate(test_frame, 30)
    print(f"\nAfter 30° rotation:")
    print(f"Channel levels: {rotated[0, :]}")

    # Rotate by 90° (should move toward right surround)
    rotated = rotator.rotate(test_frame, 90)
    print(f"\nAfter 90° rotation:")
    print(f"Channel levels: {rotated[0, :]}")
