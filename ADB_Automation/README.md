# STB Android Test Suite

Automated endurance testing tool for Android-based Set-Top Boxes (STB) via ADB (Android Debug Bridge).

Designed for long-duration tests (12h, 24h+) with automatic reconnection handling, detailed logging, and modular test structure.

## Features

- **Multi-project support** - Organize tests by project with independent configurations
- **Automatic reconnection** - Detects connection failures and reconnects without manual intervention
- **CEC auto-disable** - Disables HDMI-CEC on the device before tests to prevent interference (Android 14 compatible)
- **Detailed logging** - Timestamped logs saved to file with loop counters
- **Standby detection** - Monitors device power state and handles standby events
- **Screen session validation** - Ensures tests run inside a `screen` session for stability

## Requirements

- Python 3.6+
- ADB (Android Debug Bridge) installed and in PATH
- Android STB connected to the same network
- Linux terminal with `screen` installed (recommended for long tests)

## Installation

```bash
git clone https://github.com/gabriellaskos/android-automation-test-suite.git
cd stb-android-test-suite


## Usage

### 1. Start a screen session (recommended for long tests)

shellscript
screen -S stb_test


### 2. Run the script

shellscript
python3 stb_menu.py


### 3. Select a project and test

plaintext
============================================================
        STB TEST SUITE - SELECT PROJECT
============================================================
1 - Project 1
2 - Project 2
3 - Project 3
0 - Exit
============================================================


### 4. Choose the test type

plaintext
============================================================
        PROJECT 1 - AVAILABLE TESTS
============================================================
1 - Zapping
2 - Navigation
3 - Apps
4 - StandbyWakeup
5 - Volume Control
0 - Back to main menu
============================================================


### 5. Configure and run

- Enter device IP address (connected ADB devices are listed automatically)
- Choose test duration (12h, 24h, or custom)
- Enter a log name (max 50 characters)
- Test starts automatically


## Available Tests

| Test | Description
|-----|-----
| **Zapping** | Channel UP/DOWN cycling to test tuner stability
| **Navigation** | Complex UI navigation sequences (directional keys, OK, back)
| **Apps** | Opens and closes streaming apps (Netflix, YouTube, Disney+, Spotify, etc.)
| **StandbyWakeup** | Standby/wake-up power cycling
| **Volume Control** | Volume UP/DOWN and mute toggle cycling


## Reconnection System

The script includes an automatic reconnection system that:

1. **Detects failures** - Monitors ADB command responses for errors and timeouts
2. **Attempts reconnection** - Loops until the device is reachable again or test time expires
3. **Reinitializes sequence** - Executes the initial setup commands after reconnecting
4. **Restarts test loop** - Resumes the test from the beginning of the sequence


plaintext
[2025-01-19 14:32:15] Error sending KEY_RIGHT: timeout
[2025-01-19 14:32:15] Attempting device reconnection...
[2025-01-19 14:32:30] Reconnection successful! Restarting command sequence...
[2025-01-19 14:33:00] KEY_HOME sent successfully
[2025-01-19 14:33:10] RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING
[2025-01-19 14:33:10] === EXECUTING INITIAL SEQUENCE ===


## Architecture

plaintext
STBTester (class)
├── Connection & Communication
│   ├── f_connect_device()        # ADB connection
│   ├── f_is_device_ready()       # Device state check
│   ├── f_is_in_standby()         # Standby detection
│   └── f_disable_cec()           # CEC disable (7 methods for Android 14)
│
├── Key Commands
│   ├── f_send_key()              # Base function for all keys
│   ├── f_send_home_key()         # HOME (code 3)
│   ├── f_send_up/down/left/right_key()  # Navigation
│   ├── f_send_channelUP/DOWN_key()      # Channel control
│   ├── f_send_volume_up/down_key()      # Volume control
│   └── f_send_mute_key()                # Mute toggle
│
├── Reconnection
│   ├── f_reconnect_and_reinitialize()          # Standard reconnection
│   ├── f_reconnect_and_reinitialize_p1_zapping() # Project-specific
│   ├── f_check_and_send()                      # Standard check + send
│   └── f_check_and_send_p1_zapping()           # Project-specific
│
└── Tests
    ├── f_test_zapping_standard()    # Channel cycling
    ├── f_test_zapping_project1()    # Project 1 zapping variant
    ├── f_test_navigation_*()        # UI navigation per project
    ├── f_test_apps()                # App open/close cycling
    ├── f_test_standby_wakeup()      # Power cycling
    └── f_test_volume_control()      # Volume/mute cycling


## Logs

All logs are saved to the `logs_stb/` directory with the format:

plaintext
{custom_name}_{YYYYMMDD_HHMM}.txt


Example log output:

plaintext
[2025-01-19 10:00:00] === STARTING ZAPPING STANDARD TEST ===
[2025-01-19 10:00:01] Disabling CEC (Consumer Electronics Control)...
[2025-01-19 10:00:05] CEC disabled successfully
[2025-01-19 10:00:05] === EXECUTING INITIAL SEQUENCE ===
[2025-01-19 10:00:15] KEY_HOME sent successfully
[2025-01-19 10:00:20] KEY_FLOW sent successfully
[2025-01-19 10:00:20] === INITIAL SEQUENCE COMPLETED ===
[2025-01-19 10:00:40] KEY_CHANNEL_UP sent successfully
[2025-01-19 10:01:00] KEY_CHANNEL_DOWN sent successfully
[2025-01-19 10:01:00] ZAPPING LOOP 1 CONCLUDED


## Android Key Codes Reference

| Key | Code | Usage
|-----|-----
| HOME | 3 | Return to home screen
| BACK | 4 | Navigate back
| DPAD_UP | 19 | Navigate up
| DPAD_DOWN | 20 | Navigate down
| DPAD_LEFT | 21 | Navigate left
| DPAD_RIGHT | 22 | Navigate right
| DPAD_CENTER | 23 | OK/Select
| VOLUME_UP | 24 | Increase volume
| VOLUME_DOWN | 25 | Decrease volume
| POWER | 26 | Standby
| MUTE | 164 | Toggle mute
| CHANNEL_UP | 166 | Next channel
| CHANNEL_DOWN | 167 | Previous channel
| GUIDE | 172 | Open program guide
| WAKEUP | 224 | Wake device