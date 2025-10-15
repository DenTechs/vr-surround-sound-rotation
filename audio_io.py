"""
Real-time Audio I/O handling
Manages audio input/output using sounddevice
"""

import numpy as np
import sounddevice as sd


class AudioIO:
    """Handles real-time stereo input and surround output"""

    def __init__(
        self,
        sample_rate=48000,
        block_size=512,
        input_device=None,
        output_device=None,
        output_channels=8,
    ):
        """
        Initialize audio I/O

        Args:
            sample_rate: Audio sample rate in Hz
            block_size: Number of samples per processing block
            input_device: Input device ID or name (None for default)
            output_device: Output device ID or name (None for default)
            output_channels: Number of output channels (6 for 5.1, 8 for 7.1)
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.input_device = input_device
        self.output_device = output_device
        self.output_channels = output_channels
        self.stream = None
        self.callback = None

    def list_devices(self):
        """List all WASAPI audio devices with their capabilities"""
        print("\n" + "="*70)
        print("AUDIO DEVICES (WASAPI only)")
        print("="*70)

        devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        wasapi_found = False
        for i, device in enumerate(devices):
            in_ch = device['max_input_channels']
            out_ch = device['max_output_channels']
            hostapi_name = hostapis[device['hostapi']]['name']

            # Only show WASAPI devices
            if 'WASAPI' not in hostapi_name:
                continue

            wasapi_found = True
            markers = []
            if in_ch >= 2:
                markers.append(f"IN:{in_ch}")
            if out_ch >= 8:
                markers.append(f"OUT:{out_ch}✓")
            elif out_ch > 0:
                markers.append(f"OUT:{out_ch}")

            markers.append("WASAPI")

            marker_str = f" [{', '.join(markers)}]" if markers else ""

            print(f"[{i}] {device['name']}{marker_str}")

        if not wasapi_found:
            print("\n⚠ No WASAPI devices found!")
            print("\nShowing first 5 devices from other APIs:")
            print("-" * 70)
            count = 0
            for i, device in enumerate(devices):
                if count >= 5:
                    break
                in_ch = device['max_input_channels']
                out_ch = device['max_output_channels']
                hostapi_name = hostapis[device['hostapi']]['name']

                markers = []
                if in_ch >= 2:
                    markers.append(f"IN:{in_ch}")
                if out_ch > 0:
                    markers.append(f"OUT:{out_ch}")
                markers.append(hostapi_name)

                marker_str = f" [{', '.join(markers)}]" if markers else ""
                print(f"[{i}] {device['name']}{marker_str}")
                count += 1

            print("\nNote: WASAPI devices provide lower latency on Windows.")
            print("If you see MME/DirectSound devices, try updating audio drivers.")

        print("\n" + "="*70)
        print("⚠ WARNING: Device IDs may change when devices are plugged/unplugged!")
        print("For reliability, use device names (strings) instead of IDs in config.py")
        print("\nExamples:")
        print('  INPUT_DEVICE = "Speakers (VB-Audio Virtual Cable)"  # Recommended: use name')
        print("  INPUT_DEVICE = 27              # May change when devices added/removed")
        print("="*70)

    def get_device_info(self, device_id):
        """
        Get detailed information about a specific device

        Args:
            device_id: Device ID number
        """
        try:
            device = sd.query_devices(device_id)
            hostapis = sd.query_hostapis()
            hostapi_name = hostapis[device['hostapi']]['name']

            print(f"\nDevice [{device_id}] Details:")
            print(f"  Name: {device['name']}")
            print(f"  Host API: {hostapi_name}")
            print(f"  Input Channels: {device['max_input_channels']}")
            print(f"  Output Channels: {device['max_output_channels']}")
            print(f"  Default Sample Rate: {device['default_samplerate']} Hz")
            print(f"  Default Low Input Latency: {device['default_low_input_latency']*1000:.1f} ms")
            print(f"  Default Low Output Latency: {device['default_low_output_latency']*1000:.1f} ms")
            return device
        except Exception as e:
            print(f"Error getting device info: {e}")
            return None

    def start_stream(self, audio_callback):
        """
        Start the audio stream with the provided callback

        Args:
            audio_callback: Function with signature:
                callback(stereo_input) -> surround_output
                where stereo_input is shape (block_size, 2)
                and surround_output is shape (block_size, 8)
        """
        self.callback = audio_callback

        # Validate devices before opening stream
        try:
            if self.input_device is not None:
                input_info = sd.query_devices(self.input_device)

                # Check if this device can capture stereo
                if input_info['max_input_channels'] < 2:
                    raise ValueError(
                        f"Input device [{self.input_device}] '{input_info['name']}' "
                        f"only has {input_info['max_input_channels']} input channel(s). "
                        f"Need at least 2 input channels for stereo capture.\n\n"
                        f"For virtual audio devices:\n"
                        f"  - Look for 'VB-CABLE Input' or similar (the input side captures output audio)\n"
                        f"  - Or use a device with actual input channels\n"
                        f"Run 'python audio_io.py' to see compatible devices."
                    )

            if self.output_device is not None:
                output_info = sd.query_devices(self.output_device)
                required_channels = self.output_channels
                format_name = "5.1" if required_channels == 6 else "7.1"

                if output_info['max_output_channels'] < required_channels:
                    raise ValueError(
                        f"Output device [{self.output_device}] '{output_info['name']}' "
                        f"only has {output_info['max_output_channels']} output channel(s). "
                        f"Need {required_channels} channels for {format_name} surround.\n\n"
                        f"Run 'python audio_io.py' to find compatible devices."
                    )
        except Exception as e:
            print(f"\n{'='*60}")
            print("ERROR: Invalid audio device configuration")
            print('='*60)
            raise

        def sd_callback(indata, outdata, frames, time, status):
            if status:
                print(f"Audio status: {status}")

            # Process audio through the callback
            try:
                # Ensure input is correct shape
                if indata.shape[1] < 2:
                    # Mono input - duplicate to stereo
                    stereo = np.column_stack([indata[:, 0], indata[:, 0]])
                else:
                    stereo = indata[:, :2]

                # Process
                result = self.callback(stereo.astype(np.float32))

                # Ensure output is correct shape
                if result.shape[1] != self.output_channels:
                    print(f"Warning: Expected {self.output_channels} output channels, got {result.shape[1]}")
                    # Pad with zeros if needed
                    if result.shape[1] < self.output_channels:
                        padded = np.zeros((frames, self.output_channels), dtype=np.float32)
                        padded[:, :result.shape[1]] = result
                        result = padded

                outdata[:] = result[:, :outdata.shape[1]]

            except Exception as e:
                print(f"Error in audio callback: {e}")
                outdata.fill(0)

        # For now, disable automatic WASAPI loopback detection
        # User should select a device that already supports input (like VB-Audio Cable Input)
        # or a WASAPI loopback device that appears as an input device

        # Create normal duplex stream
        self.stream = sd.Stream(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            device=(self.input_device, self.output_device),
            channels=(2, self.output_channels),  # 2 input (stereo), 6/8 output
            dtype=np.float32,
            callback=sd_callback,
        )

        self.stream.start()
        format_name = "5.1" if self.output_channels == 6 else "7.1"
        print(f"\nAudio stream started:")
        print(f"  Sample rate: {self.sample_rate} Hz")
        print(f"  Block size: {self.block_size} samples")
        print(f"  Latency: ~{self.block_size / self.sample_rate * 1000:.1f} ms")
        print(f"  Input: {self.stream.device[0]} (stereo)")
        print(f"  Output: {self.stream.device[1]} ({format_name} surround)")

    def stop_stream(self):
        """Stop the audio stream"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("\nAudio stream stopped")

    def is_active(self):
        """Check if stream is currently active"""
        return self.stream is not None and self.stream.active


if __name__ == "__main__":
    # Test audio I/O with command-line arguments
    import sys

    audio_io = AudioIO()

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        # Show specific device info
        device_id = int(sys.argv[1])
        audio_io.get_device_info(device_id)
    else:
        # List WASAPI devices
        audio_io.list_devices()

    print("\nUsage:")
    print("  python audio_io.py      - List WASAPI devices")
    print("  python audio_io.py <ID> - Show details for specific device ID")
