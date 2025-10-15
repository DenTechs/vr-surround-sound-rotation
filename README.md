# VR Surround Audio Rotation

This program captures game audio, upmixes it to 5.1/7.1 surround, and rotates the soundfield based on VR headset tracking. This allows you to use a VR headset with a real surround sound speaker setup (I.E. if you have a home theater setup) while always keeping the audio sounding like its in front of you. Due to upmixing from stereo rather than having native surround sound in games, this has the limitation that you cannot differentiate sounds coming from the front or back easily.
To be fully upfront, most of the code was written using AI as this was weekend proof-of-concept-for-fun kind of project, take anything written past this point with a grain of salt.

**Simple to use:** Just install a virtual audio device and run `python main.py`

## Audio Flow

```
Game Audio Output → Virtual Audio Device → This Program → 5.1/7.1 Physical Speakers
                    (VB-Audio Cable)      (Upmix + Rotate)
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Virtual Audio Device

You need a virtual audio device to route game audio to the program:

**Option A: VB-Audio Virtual Cable (Recommended)**
1. Download and install from https://vb-audio.com/Cable/
2. Set your game audio output to "CABLE Input (VB-Audio Virtual Cable)"
3. The program will capture from "CABLE Output (VB-Audio Virtual Cable)"

**Option B: Stereo Mix (Windows built-in)**
1. Right-click speaker icon → Sounds → Recording tab
2. Right-click empty space → Show Disabled Devices
3. Right-click "Stereo Mix" → Enable
4. Note: This captures ALL system audio

**Option C: Voicemeeter**
1. Download from https://vb-audio.com/Voicemeeter/
2. Route game audio through Voicemeeter virtual outputs

### 3. Configure Audio Devices

**Find your device IDs/names:**
```bash
python main.py
# If presented with option selection, select option 5: "Check audio devices and exit"
```

This shows WASAPI devices with their capabilities:
- **Input**: Virtual audio device (VB-Audio Cable Output, Stereo Mix, etc.)
- **Output**: Your 5.1/7.1 surround sound system (must have 6 or 8 channels)

**Edit `config.py`** with your devices:

⚠ **Important:**
1. Device IDs can change when audio devices are plugged/unplugged
2. Include ", Windows WASAPI" to avoid ambiguity (some devices have MME/DirectSound/WASAPI versions)

```python
# Recommended: Use full device name with API (copy from device list)
INPUT_DEVICE = "CABLE Output (VB-Audio Virtual Cable), Windows WASAPI"
OUTPUT_DEVICE = "Speakers (Realtek High Definition Audio), Windows WASAPI"

# Alternative: Use device IDs (NOT recommended - they change!)
INPUT_DEVICE = 27
OUTPUT_DEVICE = 23
```

### 4. Run the Program

```bash
python main.py
```

The program will show a mode selection menu:
1. **OpenVR** - Track VR headset (requires SteamVR running)
2. **Test - Continuous rotation** - 30°/sec rotation for testing
3. **Test - Sweep** - Back/forth sweep pattern
4. **Test - Static** - Manual angle entry
5. **Check audio devices** - List WASAPI devices and exit

## Configuration

Edit `config.py` to customize:

### Operating Mode
```python
MODE = "ask"  # Show menu at startup
# or
MODE = "openvr"        # Always use VR headset
MODE = "test_rotate"   # Always use rotation test
MODE = "test_sweep"    # Always use sweep test
MODE = "test_static"   # Always use static test

AUTO_START = False  # Skip "Press Enter" when MODE is set
```

### Audio Settings
```python
SAMPLE_RATE = 48000      # Hz
BLOCK_SIZE = 512         # Samples (lower = less latency)
SURROUND_FORMAT = "7.1"  # Options: "stereo", "5.1", or "7.1"
```

### Rotation Settings
```python
SMOOTHING_FACTOR = 0.85  # 0-1, higher = smoother but more lag
                         # 0.85 recommended
                         # 0.95 = very smooth, noticeable lag
                         # 0.70 = responsive, slight jitter
```

## File Structure

### Core Files
- `main.py` - Main application with mode selection (run this!)
- `config.py` - Configuration settings
- `audio_io.py` - Real-time audio I/O (internal module)
- `openvr_tracker.py` - VR headset tracking and test modes (internal module)

### Audio Processing (internal modules)
- `upmix.py` - Stereo to 5.1/7.1 upmixing algorithm
- `rotation.py` - Surround soundfield rotation engine
- `stereo_rotation.py` - Stereo rotation (debug mode)

### Utilities
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - This file
- `DEVICE_SETUP.md` - Detailed device configuration guide

## Usage Examples

### Check Available Devices
```bash
python main.py
# Select option 5: "Check audio devices and exit"
```

### Run with OpenVR (VR Headset)
```bash
# Set MODE = "openvr" in config.py, then:
python main.py
```
Requires SteamVR to be running.

### Run in Test Mode (No VR Hardware)
```bash
# Set MODE = "test_rotate" in config.py, then:
python main.py
```
Useful for testing without VR hardware.

### Interactive Mode Selection
```bash
# Set MODE = "ask" in config.py (default), then:
python main.py
# Choose from menu: OpenVR, test modes, or check devices
```

## Supported Formats

- **Stereo (2.0)**: L, R (debug mode, no upmix)
- **5.1 Surround**: L, R, C, LFE, LS, RS
- **7.1 Surround**: L, R, C, LFE, LS, RS, LB, RB

Set `SURROUND_FORMAT` in `config.py`.

## Troubleshooting

### "No WASAPI devices found"
- Ensure you're on Windows
- Update audio drivers from manufacturer's website
- WASAPI should be available on Windows Vista and later
- If only MME/DirectSound devices appear, the program will still work but with higher latency
- Install VB-Audio Virtual Cable or enable Stereo Mix for virtual audio routing

### "Failed to initialize OpenVR"
- Make sure SteamVR is running
- VR headset is connected and tracked
- Or use a test mode instead

### "Invalid audio device configuration"
- Run `python main.py` and select option 5 to check device IDs/names
- Verify INPUT_DEVICE has input channels
- Verify OUTPUT_DEVICE has 6 or 8 output channels
- **Device IDs changed?** This happens when devices are added/removed. Use device names (strings) instead of IDs for reliability

### "Multiple input/output devices found for..."
**Cause**: Your device name matches multiple devices with different APIs (MME, DirectSound, WASAPI)

**Solution**: Include the API type in your device name:
```python
# Before (ambiguous):
INPUT_DEVICE = "Speakers (Realtek Audio)"

# After (specific):
INPUT_DEVICE = "Speakers (Realtek Audio), Windows WASAPI"
```

Run `python main.py` → option 5 to see the full device names with API suffixes, then copy the exact string.

### High Latency
- Decrease `BLOCK_SIZE` in config.py (try 256 or 128)
- Use WASAPI devices instead of MME/DirectSound

### Audio Glitches/Crackling
- Increase `BLOCK_SIZE` in config.py (try 1024 or 2048)
- Check CPU usage
- Close other audio applications

## Tips

- **Use device names, not IDs** - Device IDs change when USB devices are plugged/unplugged. Use device name strings in config.py for reliability
- **WASAPI devices** provide lowest latency
- **Block size** trade-off: Lower = less latency, higher = less CPU usage
- **Test modes** are great for verifying setup without VR hardware
- Set `AUTO_START = True` and `MODE = "openvr"` for automatic startup
- Use `SURROUND_FORMAT = "stereo"` for debugging rotation without upmix

## Technical Details

The program uses:
- **Stereo Upmix**: Phase-based center extraction, decorrelated surrounds
- **Amplitude Panning**: Constant-power panning between adjacent speakers
- **Rotation**: ITU-R BS.775-3 standard speaker positions
- **Smoothing**: Exponential moving average for smooth head tracking
