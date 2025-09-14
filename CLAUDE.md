# LED Analyzer Testing Guide

## How to Test the LED Analyzer

### Setup
1. Activate the virtual environment:
   ```bash
   source led_env/bin/activate
   ```

2. Run the LED analyzer:
   ```bash
   python led_analyzer.py
   ```

### Testing Methods

#### Quick Test (Single Frame)
- Choose option 3: "Single frame analysis"
- The application will capture one frame and analyze it
- Output shows: `Green LED detected: YES/NO` 

#### Diode Functionality Test
To confirm a diode is working properly:
1. Choose option 3 for single frame analysis
2. Take 3 measurements, each 2 seconds apart
3. **The diode is working if it appears in at least 2 out of 3 measurements**

#### Continuous Monitoring
- Choose option 1: "Continuous analysis with live feed"
- Shows real-time LED detection every 2 seconds
- Press 'q' to quit

#### Blinking Pattern Analysis
- Choose option 2: "Blinking pattern analysis"
- Monitors LED states over a specified duration (default 10 seconds)
- Calculates blinking frequency and pattern changes

### Expected LED Color
- expected green LED color is 0, 255, 0

### Debug Information
- All debug files are saved to `tmp/` directory:
  - `debug_frame_<timestamp>.jpg` - Images that Claude analyzes
  - `debug_<timestamp>.txt` - Complete debug logs with prompts and responses

### API Configuration
- API key is automatically loaded from `api_key.txt`
- Fallback to environment variable `ANTHROPIC_API_KEY`
- Uses Claude Sonnet 4 model for analysis

Always use virtualn environment to run python part of video led test the application.
