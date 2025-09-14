This is a project for ESP32-S3 Mini ESP32-S3FH4R2 Dual-Core Processor, 240MHz ESP32-S3-Zero board.
It documentation is here: https://www.waveshare.com/wiki/ESP32-S3-Zero
Mini version has less board_build and board_upload flash_size.
I want to make a program with pio (PlatformIO) , using c language with ESP-IDF framework.
App on the board should will blink the onboard LED in green. Turn it on for three seconds and then off for one.
The board is connected to /dev/ttyACM0.
The diode number and details are in documentation.
Check if selected board is the correct one and exist in board list and if it has the same amount of ram.
Upload the code and test it. If it works, confirm success. Repeat until it works.
Make sure to include all necessary libraries and configurations for the ESP32-S3 mini board.
