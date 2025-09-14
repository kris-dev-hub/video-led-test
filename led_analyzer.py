import cv2
import os
import numpy as np
import base64
import time
from datetime import datetime
import anthropic
from PIL import Image
import io
import json

class LEDAnalyzer:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.cap = None
        self.running = False

    def initialize_camera(self, camera_index=0):
        """Initialize camera capture"""
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise Exception(f"Could not open camera {camera_index}")

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

    def capture_frame(self):
        """Capture a single frame from camera"""
        if not self.cap:
            raise Exception("Camera not initialized")

        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Failed to capture frame")

        return frame

    def frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 for API"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)

        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG')
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        return base64_image

    def analyze_led_with_claude(self, frame, save_debug_image=False):
        """Send frame to Claude API for LED analysis"""
        base64_image = self.frame_to_base64(frame)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        # Save debug image if requested
        if save_debug_image:
            debug_filename = f"tmp/debug_frame_{timestamp}.jpg"
            cv2.imwrite(debug_filename, frame)

        # Define the prompt
        prompt_text = """Analyze this image and identify any LED lights. For each LED you find, please provide:
1. The color of the LED (red, green, blue, yellow, white, etc.)
2. The brightness level (dim, medium, bright)
3. The approximate position in the image
4. Whether it appears to be on or off

Please format your response as JSON ONLY with the following structure (no markdown formatting):
{
    "leds_detected": [
        {
            "color": "color_name",
            "brightness": "brightness_level",
            "position": "description_of_position",
            "status": "on/off"
        }
    ],
    "total_leds": number
}"""

        debug_info = []
        debug_info.append(f"Timestamp: {timestamp}")
        debug_info.append(f"Prompt sent to Claude:\n{prompt_text}\n")

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }]
            )

            response = message.content[0].text
            debug_info.append(f"Claude response:\n{response}\n")

            # Save debug info to file
            if save_debug_image:
                debug_txt_filename = f"tmp/debug_{timestamp}.txt"
                with open(debug_txt_filename, 'w') as f:
                    f.write('\n'.join(debug_info))

            # Check for green LEDs and provide simple output
            has_green_led = False
            try:
                # Clean the response - remove markdown formatting if present
                clean_result = response.strip()
                if clean_result.startswith('```json'):
                    clean_result = clean_result[7:]
                if clean_result.endswith('```'):
                    clean_result = clean_result[:-3]
                clean_result = clean_result.strip()

                led_data = json.loads(clean_result)
                for led in led_data.get('leds_detected', []):
                    if 'green' in led.get('color', '').lower() and led.get('status', '').lower() == 'on':
                        has_green_led = True
                        break
            except:
                pass

            print(f"Green LED detected: {'YES' if has_green_led else 'NO'}")

            return response

        except Exception as e:
            error_msg = f"Error calling Claude API: {e}"
            debug_info.append(error_msg)
            if save_debug_image:
                debug_txt_filename = f"tmp/debug_{timestamp}.txt"
                with open(debug_txt_filename, 'w') as f:
                    f.write('\n'.join(debug_info))
            print(error_msg)
            return None

    def detect_blinking(self, duration_seconds=10):
        """Detect blinking patterns over a specified duration"""
        print(f"Analyzing blinking patterns for {duration_seconds} seconds...")

        led_states = []
        start_time = time.time()
        frame_count = 0

        while time.time() - start_time < duration_seconds:
            frame = self.capture_frame()

            # Analyze every 5th frame to reduce API calls
            if frame_count % 5 == 0:
                result = self.analyze_led_with_claude(frame, save_debug_image=True)
                if result:
                    try:
                        # Clean the response - remove markdown formatting if present
                        clean_result = result.strip()
                        if clean_result.startswith('```json'):
                            clean_result = clean_result[7:]
                        if clean_result.endswith('```'):
                            clean_result = clean_result[:-3]
                        clean_result = clean_result.strip()

                        led_data = json.loads(clean_result)
                        timestamp = time.time() - start_time
                        led_states.append({
                            'timestamp': timestamp,
                            'leds': led_data.get('leds_detected', [])
                        })
                        print(f"Frame {frame_count//5}: {len(led_data.get('leds_detected', []))} LEDs detected")
                    except json.JSONDecodeError as e:
                        print(f"Could not parse Claude response: {result}")
                        print(f"JSON Error: {e}")

            frame_count += 1
            time.sleep(0.1)  # Small delay between frames

        return self.analyze_blinking_pattern(led_states)

    def analyze_blinking_pattern(self, led_states):
        """Analyze the collected LED states to determine blinking frequency"""
        if not led_states:
            return {"error": "No LED data collected"}

        # Group by LED position/color to track individual LEDs
        led_timelines = {}

        for state in led_states:
            timestamp = state['timestamp']
            for led in state['leds']:
                led_key = f"{led.get('color', 'unknown')}_{led.get('position', 'unknown')}"

                if led_key not in led_timelines:
                    led_timelines[led_key] = []

                led_timelines[led_key].append({
                    'timestamp': timestamp,
                    'status': led.get('status', 'unknown'),
                    'brightness': led.get('brightness', 'unknown')
                })

        # Calculate blinking frequency for each LED
        results = {}
        for led_key, timeline in led_timelines.items():
            blink_count = 0
            last_status = None

            for entry in timeline:
                current_status = entry['status']
                if last_status and last_status != current_status:
                    blink_count += 1
                last_status = current_status

            duration = led_states[-1]['timestamp'] - led_states[0]['timestamp']
            frequency = blink_count / (2 * duration) if duration > 0 else 0  # Divide by 2 since one blink = on->off->on

            results[led_key] = {
                'blink_frequency_hz': frequency,
                'total_state_changes': blink_count,
                'duration_analyzed': duration
            }

        return results

    def run_continuous_analysis(self):
        """Run continuous LED analysis with live video feed"""
        print("Starting continuous LED analysis. Press 'q' to quit.")

        self.running = True
        last_analysis_time = 0

        while self.running:
            frame = self.capture_frame()

            # Show live video feed (only if GUI available)
            try:
                cv2.imshow('LED Analyzer - Press q to quit', frame)
            except cv2.error:
                # Skip display in headless environments
                pass

            # Analyze frame every 2 seconds to avoid API rate limits
            current_time = time.time()
            if current_time - last_analysis_time > 2:
                print("Analyzing current frame...")
                result = self.analyze_led_with_claude(frame)
                if result:
                    print(f"Analysis result: {result}")
                last_analysis_time = current_time

            # Check for quit key
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            # Ignore GUI cleanup errors in headless environments
            pass
        self.running = False

def main():
    # Get API key from file, environment, or user input
    api_key = None

    # Try to read from api_key.txt file
    try:
        with open('api_key.txt', 'r') as f:
            api_key = f.read().strip()
        print("API key loaded from api_key.txt")
    except FileNotFoundError:
        pass

    # Fall back to environment variable
    if not api_key:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            print("API key loaded from environment variable")

    # Fall back to user input
    if not api_key:
        api_key = input("Enter your Anthropic API key (or set ANTHROPIC_API_KEY env var): ").strip()

    if not api_key:
        print("API key is required!")
        return

    try:
        analyzer = LEDAnalyzer(api_key)
        analyzer.initialize_camera()

        print("LED Analyzer initialized successfully!")
        print("Choose an option:")
        print("1. Continuous analysis with live feed")
        print("2. Blinking pattern analysis (10 seconds)")
        print("3. Single frame analysis")

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            analyzer.run_continuous_analysis()
        elif choice == "2":
            duration = input("Enter analysis duration in seconds (default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            results = analyzer.detect_blinking(duration)
            print("\nBlinking analysis results:")
            print(json.dumps(results, indent=2))
        elif choice == "3":
            frame = analyzer.capture_frame()
            print("Analyzing single frame...")
            result = analyzer.analyze_led_with_claude(frame, save_debug_image=True)
            print(f"Analysis result: {result}")
        else:
            print("Invalid choice!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'analyzer' in locals():
            analyzer.cleanup()

if __name__ == "__main__":
    main()