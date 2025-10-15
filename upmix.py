"""
Stereo to surround upmix algorithm
Converts 2-channel stereo to 5.1 or 7.1 surround
"""

import numpy as np
from scipy import signal


class StereoTo71Upmixer:
    """Upmixes stereo audio to 5.1 or 7.1 surround sound"""

    def __init__(self, sample_rate=48000, format="7.1"):
        """
        Initialize upmixer

        Args:
            sample_rate: Audio sample rate in Hz
            format: "5.1" or "7.1" surround format
        """
        self.sample_rate = sample_rate
        self.format = format
        self.num_channels = 6 if format == "5.1" else 8

        # Create decorrelation filters using all-pass filters
        # This adds slight phase differences to create spatial impression
        self._setup_decorrelation_filters()

        # Low-pass filter for LFE channel (80 Hz cutoff)
        self.lfe_filter = self._create_lfe_filter()

    def _setup_decorrelation_filters(self):
        """Create all-pass filters for decorrelating surround channels"""
        # Simple all-pass filter coefficients for phase shift
        # These create subtle differences between channels
        self.surround_delay_samples = int(0.005 * self.sample_rate)  # 5ms delay
        self.rear_delay_samples = int(0.010 * self.sample_rate)  # 10ms delay

    def _create_lfe_filter(self):
        """Create low-pass filter for LFE channel (subwoofer)"""
        nyquist = self.sample_rate / 2
        cutoff = 80  # Hz
        sos = signal.butter(4, cutoff / nyquist, btype='low', output='sos')
        return sos

    def upmix(self, stereo_frame):
        """
        Upmix a stereo frame to 5.1 or 7.1 surround

        Args:
            stereo_frame: numpy array of shape (num_samples, 2) - stereo audio

        Returns:
            numpy array of shape (num_samples, 6 or 8) - surround audio
            5.1 channel order: L, R, C, LFE, LS, RS
            7.1 channel order: L, R, C, LFE, LS, RS, LB, RB
        """
        num_samples = stereo_frame.shape[0]
        output = np.zeros((num_samples, self.num_channels), dtype=np.float32)

        left = stereo_frame[:, 0]
        right = stereo_frame[:, 1]

        # Front Left and Right - pass through
        output[:, 0] = left
        output[:, 1] = right

        # Center - sum of L+R with reduced level
        # Extracted center content (common to both channels)
        output[:, 2] = (left + right) * 0.5

        # LFE - low-pass filtered sum for subwoofer
        lfe_sum = (left + right) * 0.5
        output[:, 3] = signal.sosfilt(self.lfe_filter, lfe_sum)

        # Side Surrounds (LS, RS) - decorrelated with phase shift
        # Use difference signal for ambient content
        diff_left = left - right
        diff_right = right - left

        # Add slight delay for decorrelation
        ls_signal = np.concatenate([
            np.zeros(self.surround_delay_samples),
            diff_left
        ])[:num_samples] * 0.7

        rs_signal = np.concatenate([
            np.zeros(self.surround_delay_samples),
            diff_right
        ])[:num_samples] * 0.7

        output[:, 4] = ls_signal
        output[:, 5] = rs_signal

        # Rear Surrounds (LB, RB) - only for 7.1
        if self.format == "7.1":
            # Use inverted and delayed difference signals
            lb_signal = np.concatenate([
                np.zeros(self.rear_delay_samples),
                -diff_left
            ])[:num_samples] * 0.5

            rb_signal = np.concatenate([
                np.zeros(self.rear_delay_samples),
                -diff_right
            ])[:num_samples] * 0.5

            output[:, 6] = lb_signal
            output[:, 7] = rb_signal

        return output


if __name__ == "__main__":
    # Test the upmixer
    import sounddevice as sd

    upmixer = StereoTo71Upmixer()

    # Generate test stereo signal (1 second, 440 Hz tone)
    duration = 1.0
    sample_rate = 48000
    t = np.linspace(0, duration, int(sample_rate * duration))

    # Stereo test: left=440Hz, right=880Hz
    stereo = np.column_stack([
        np.sin(2 * np.pi * 440 * t),
        np.sin(2 * np.pi * 880 * t)
    ]).astype(np.float32)

    # Upmix to 7.1
    surround = upmixer.upmix(stereo)

    print(f"Input shape: {stereo.shape}")
    print(f"Output shape: {surround.shape}")
    print("Channel order: L, R, C, LFE, LS, RS, LB, RB")
    print("\nUpmix successful!")
