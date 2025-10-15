"""
Configuration file for audio rotation system
Adjust these settings based on your hardware and preferences
"""

# Operating Mode
MODE = "ask"  # Options:
              # "ask" - Show menu at startup to choose mode
              # "openvr" - Use VR headset tracking (requires SteamVR)
              # "test_rotate" - Continuous rotation test (30°/sec)
              # "test_sweep" - Sweep back/forth test
              # "test_static" - Manual angle entry test

AUTO_START = False  # If True, skip "Press Enter to start" prompt when MODE is set
                    # Only applies when MODE is not "ask"

# Audio Settings
SAMPLE_RATE = 48000  # Hz - standard for professional audio
BLOCK_SIZE = 512     # samples - lower = less latency, higher = less CPU

# Surround Format
SURROUND_FORMAT = "7.1"  # Options: "stereo", "5.1", or "7.1"
                         # stereo = 2 channels: L, R (debug mode, no upmix)
                         # 5.1 = 6 channels: L, R, C, LFE, LS, RS
                         # 7.1 = 8 channels: L, R, C, LFE, LS, RS, LB, RB

# Device Selection (None = show device list at startup)
# Run 'python audio_io.py' to list available WASAPI devices and get their IDs
#
# ⚠ WARNING: Device IDs may change when audio devices are added/removed!
# For reliability, use device name strings instead of IDs:
#
# Examples using device names (recommended):
#   INPUT_DEVICE = "CABLE Output"  # Substring match works
#   OUTPUT_DEVICE = "Speakers (Realtek High Definition Audio)"
#
# Examples using device IDs (may change):
#   INPUT_DEVICE = 27
#   OUTPUT_DEVICE = 23
#
INPUT_DEVICE = None   # Set to device ID (int), device name (str), or None
OUTPUT_DEVICE = None  # Set to device ID (int), device name (str), or None

# Rotation Settings
SMOOTHING_FACTOR = 0.85  # 0-1, higher = smoother but more lag
                         # 0.85 recommended for good balance
                         # 0.95 = very smooth, noticeable lag
                         # 0.70 = responsive, slight jitter

# Upmix Settings
LFE_CUTOFF_HZ = 80           # Low-pass filter cutoff for subwoofer
SURROUND_DECORRELATION_MS = 5  # Delay for surround decorrelation
REAR_DECORRELATION_MS = 10     # Delay for rear channel decorrelation

# Display Settings
STATUS_UPDATE_INTERVAL = 0.05  # seconds - how often to update display
