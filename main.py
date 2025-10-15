"""
Surround Audio Rotation for VR
Main application entry point
"""

import numpy as np
import time
import sys
from audio_io import AudioIO
from openvr_tracker import OpenVRTracker, TestTracker
from upmix import StereoTo71Upmixer
from rotation import SurroundRotator
from stereo_rotation import StereoRotator
import config


class AudioRotationApp:
    """Main application class"""

    def __init__(
        self,
        tracker,
        sample_rate=None,
        block_size=None,
        smoothing_factor=None,
        input_device=None,
        output_device=None,
    ):
        """
        Initialize the audio rotation application

        Args:
            tracker: Tracker object (OpenVRTracker or TestTracker)
            sample_rate: Audio sample rate in Hz (None = use config)
            block_size: Audio processing block size (None = use config)
            smoothing_factor: Smoothing for rotation (None = use config)
            input_device: Audio input device (None = use config)
            output_device: Audio output device (None = use config)
        """
        # Use config values as defaults
        self.sample_rate = sample_rate or config.SAMPLE_RATE
        self.block_size = block_size or config.BLOCK_SIZE
        self.smoothing_factor = smoothing_factor or config.SMOOTHING_FACTOR
        input_device = input_device if input_device is not None else config.INPUT_DEVICE
        output_device = output_device if output_device is not None else config.OUTPUT_DEVICE

        # Initialize components
        surround_format = config.SURROUND_FORMAT
        self.is_stereo_mode = (surround_format.lower() == "stereo")

        if self.is_stereo_mode:
            output_channels = 2
            print(f"Initializing STEREO Audio Rotation System (Debug Mode)...")
        else:
            output_channels = 6 if surround_format == "5.1" else 8
            print(f"Initializing {surround_format} Audio Rotation System...")

        print("=" * 50)

        if self.is_stereo_mode:
            # Stereo debug mode - no upmixer
            self.upmixer = None
            self.rotator = StereoRotator()
            print("✓ Stereo rotator initialized (debug mode)")
        else:
            # Normal surround mode
            self.upmixer = StereoTo71Upmixer(sample_rate=self.sample_rate, format=surround_format)
            print(f"✓ Upmixer initialized ({surround_format})")

            self.rotator = SurroundRotator(format=surround_format)
            print(f"✓ Rotation engine initialized ({surround_format})")

        self.tracker = tracker
        print("✓ Tracker initialized")

        self.audio_io = AudioIO(
            sample_rate=self.sample_rate,
            block_size=self.block_size,
            input_device=input_device,
            output_device=output_device,
            output_channels=output_channels,
        )
        print("✓ Audio I/O initialized")

        # Smoothed yaw value
        self.smoothed_yaw = 0.0

        print("=" * 50)

    def _smooth_yaw(self, new_yaw):
        """
        Apply exponential smoothing to yaw angle to prevent abrupt changes

        Args:
            new_yaw: New yaw value in degrees

        Returns:
            Smoothed yaw value
        """
        # Exponential moving average
        self.smoothed_yaw = (
            self.smoothing_factor * self.smoothed_yaw +
            (1 - self.smoothing_factor) * new_yaw
        )
        return self.smoothed_yaw

    def audio_callback(self, stereo_input):
        """
        Process audio: stereo -> [upmix] -> rotate -> output

        Args:
            stereo_input: Stereo audio input (block_size, 2)

        Returns:
            Surround output (block_size, 2/6/8 depending on format)
        """
        # Get current yaw angle and smooth it
        current_yaw = self.tracker.get_yaw()
        smoothed_yaw = self._smooth_yaw(current_yaw)

        if self.is_stereo_mode:
            # Stereo debug mode: rotate stereo directly
            rotated = self.rotator.rotate(stereo_input, smoothed_yaw)
        else:
            # Normal mode: upmix then rotate
            surround = self.upmixer.upmix(stereo_input)
            rotated = self.rotator.rotate(surround, smoothed_yaw)

        return rotated

    def run(self):
        """Start the application"""
        try:
            # List available audio devices
            print("\nScanning audio devices...")
            self.audio_io.list_devices()

            print("\n" + "=" * 50)
            print("CONFIGURATION")
            print("=" * 50)
            print(f"Sample Rate: {self.sample_rate} Hz")
            print(f"Block Size: {self.block_size} samples")
            print(f"Latency: ~{self.block_size / self.sample_rate * 1000:.1f} ms")
            print(f"Rotation Smoothing: {self.smoothing_factor}")

            # Get user confirmation (unless AUTO_START is enabled)
            if not config.AUTO_START:
                print("\nPress Enter to start, or Ctrl+C to quit...")
                input()

            # Start tracker
            self.tracker.start()

            # Start audio processing
            self.audio_io.start_stream(self.audio_callback)

            print("\n" + "=" * 50)
            print("RUNNING - Audio rotation active!")
            print("=" * 50)
            print("Press Ctrl+C to stop\n")

            # Monitor status
            while self.audio_io.is_active():
                yaw = self.tracker.get_yaw()
                smoothed = self.smoothed_yaw
                print(
                    f"\rYaw: {yaw:6.1f}° | Smoothed: {smoothed:6.1f}° | "
                    f"Rotation: {smoothed:6.1f}°",
                    end="",
                    flush=True,
                )
                time.sleep(config.STATUS_UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nStopping...")

        finally:
            self.audio_io.stop_stream()
            self.tracker.stop()
            print("Application closed")


def check_devices_and_exit():
    """Check audio devices and exit"""
    from audio_io import AudioIO
    audio_io = AudioIO()
    audio_io.list_devices()
    print("\nSet INPUT_DEVICE and OUTPUT_DEVICE in config.py with device Names or IDs")
    sys.exit(0)


def select_mode():
    """Show mode selection menu and return chosen mode"""
    print("\n" + "=" * 60)
    print("VR SURROUND AUDIO ROTATION - MODE SELECTION")
    print("=" * 60)
    print("\n1. OpenVR - Track VR headset (requires SteamVR)")
    print("2. Test - Continuous rotation (30°/sec)")
    print("3. Test - Sweep back/forth")
    print("4. Test - Manual angle entry (static)")
    print("5. Check audio devices and exit")
    print("\nPress Ctrl+C to quit")

    while True:
        try:
            choice = input("\nSelect mode [1-5]: ").strip()

            if choice == "1":
                return "openvr"
            elif choice == "2":
                return "test_rotate"
            elif choice == "3":
                return "test_sweep"
            elif choice == "4":
                return "test_static"
            elif choice == "5":
                check_devices_and_exit()
            else:
                print("Invalid choice. Please enter 1-5.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting...")
            sys.exit(0)


def create_tracker(mode):
    """Create and return appropriate tracker based on mode"""
    if mode == "openvr":
        return OpenVRTracker()
    elif mode == "test_rotate":
        return TestTracker(mode="rotate")
    elif mode == "test_sweep":
        return TestTracker(mode="sweep")
    elif mode == "test_static":
        return TestTracker(mode="static")
    else:
        raise ValueError(f"Unknown mode: {mode}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("SURROUND AUDIO ROTATION FOR VR")
    print("=" * 60)

    # Check if devices need configuration
    if config.INPUT_DEVICE is None or config.OUTPUT_DEVICE is None:
        print("\n⚠ Audio devices not configured in config.py")
        print("\nShowing available devices:")
        check_devices_and_exit()

    # Determine mode
    mode = config.MODE.lower()

    if mode == "ask":
        mode = select_mode()

    # Validate mode
    valid_modes = ["openvr", "test_rotate", "test_sweep", "test_static"]
    if mode not in valid_modes:
        print(f"\n✗ Invalid MODE in config.py: '{config.MODE}'")
        print(f"Valid modes: {', '.join(valid_modes)}, or 'ask'")
        sys.exit(1)

    # Create tracker
    print(f"\nInitializing in {mode.replace('_', ' ').upper()} mode...")
    try:
        tracker = create_tracker(mode)
    except Exception as e:
        print(f"\n✗ Failed to initialize tracker: {e}")
        sys.exit(1)

    # Create and run app
    app = AudioRotationApp(tracker)
    app.run()


if __name__ == "__main__":
    main()
