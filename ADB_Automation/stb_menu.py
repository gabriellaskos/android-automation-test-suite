# -----------------------
# Made by Gabriel Laskos -
# ------------------------
#
#!/usr/bin/env python3

import subprocess
import time
from datetime import datetime
import os
import sys

# ============================================================================
# GLOBAL SETTINGS
# ============================================================================

LOG_DIR = "logs_stb"
os.makedirs(LOG_DIR, exist_ok=True)

# ============================================================================
# MAIN CLASS - STB TESTER
# ============================================================================

class STBTester:
    """
    Main class for Android STB testing via ADB.
    Organizes all tests by project configuration.
    """
    
    def __init__(self):
        """Initialize class variables"""
        self.device = None
        self.ip = None
        self.port = 5555
        self.log_path = None
        self.error_already_shown = False

    # ========================================================================
    # LOGGING SYSTEM
    # ========================================================================
        
    def f_setup_logging(self, test_name):
        """
        Configure LOGS for specific test.
        
        Returns:
            bool: True if setup successful, False if error occurred
        """ 
        try:
            log_name = input(f"Enter a name for {test_name} log no spaces and max 50 chars: ").strip().replace(" ", "_")

            if not log_name:
                log_name = f"log_{test_name.lower()}"

            # Check characters limit
            if len(log_name) > 50:
                print("\n" + "="*60)
                print("LOG NAME TOO LONG")
                print("="*60)
                print(f"• Current length: {len(log_name)} characters")
                print("• Use a shorter name")
                print("="*60)
                print("Returning to menu in 10 seconds...")
                print("="*60)
                time.sleep(5)
                os.system("cls" if os.name == "nt" else "clear")
                return False

            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            log_filename = f"{log_name}_{timestamp}.txt"
            self.log_path = os.path.join(LOG_DIR, log_filename)
            return True
    
        except Exception as e:
            print("\n" + "="*60)
            print("LOG SETUP ERROR")
            print("="*60)
            print("• Failed to setup logging")
            print("• Log name must be max 50 characters")
            print("="*60)
            print("Returning to menu in 5 seconds...")
            print("="*60)
            time.sleep(5)
            os.system("cls" if os.name == "nt" else "clear")
            return False

    def f_log(self, msg):
        """
        Log function - writes into the console all interactions.
        
        Args:
            msg (str): Message to log
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{timestamp}] {msg}"
        print(line)
        if self.log_path:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    # ========================================================================
    # ADB CONNECTION AND COMMUNICATION
    # ========================================================================

    def f_list_connected_devices(self):
        """
        List all devices currently connected via ADB.
        Displays in a formatted table.
        """
        try:
            result = subprocess.run(["adb", "devices"], check=True, text=True, capture_output=True)
            output = result.stdout.strip()
            
            lines = output.split('\n')
            device_lines = [line.strip() for line in lines[1:] if line.strip()]
            
            if not device_lines:
                print("\n" + "="*60)
                print("NO DEVICES CONNECTED")
                print("="*60)
                print("• No ADB devices found")
                print("• Make sure ADB is enabled on the STB")
                print("• Check network connectivity")
                print("="*60 + "\n")
                return []
            
            print("\n" + "="*60)
            print("CONNECTED ADB DEVICES")
            print("="*60)
            
            devices = []
            for i, line in enumerate(device_lines, 1):
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]
                    devices.append((device_id, status))
                    
                    if ':' in device_id:
                        ip_part = device_id.split(':')[0]
                        port_part = device_id.split(':')[1]
                        print(f"{i}. IP: {ip_part} | Port: {port_part} | Status: [{status}]")
                    else:
                        print(f"{i}. Device: {device_id} | Status: [{status}]")
            
            print("="*60 + "\n")
            return devices
            
        except subprocess.CalledProcessError as e:
            print("\n" + "="*60)
            print("ADB COMMAND ERROR")
            print("="*60)
            print("• Failed to list devices")
            print("• Check if ADB is installed and in PATH")
            print(f"• Error: {e.stderr if e.stderr else 'Unknown error'}")
            print("="*60 + "\n")
            return []
        except Exception as e:
            print(f"\nError listing devices: {str(e)}\n")
            return []

    def f_connect_device(self, ip, port):
        """
        Connect to STB device via ADB.
        
        Args:
            ip (str): STB IP address
            port (int): ADB port (default 5555)
            
        Returns:
            str: Device identifier if connected, None if failed
        """
        device = f"{ip}:{port}"
        try:
            result = subprocess.run(["adb", "connect", device], check=True, text=True, capture_output=True)
            output = result.stdout.strip().lower()
            if "connected" in output or "already connected" in output:
                self.f_log(f"Successfully connected: {output}")
                time.sleep(10)
                return device
            else:
                self.f_log(f"Failed to connect: {output}")
                print("\n" + "="*60)
                print("ADB CONNECTION FAILED")
                print("="*60)
                print(f"• Target: {device}")
                print(f"• Response: {output}")
                print("• Check if ADB is enabled on STB")
                print("• Verify network connectivity")
                print("="*60)
                print("Returning to menu in 10 seconds...")
                print("="*60)
                time.sleep(10)
                os.system("cls" if os.name == "nt" else "clear")
                return None
        except subprocess.CalledProcessError as e:
            self.f_log(f"Connection error: {e.stderr.strip()}")
            print("\n" + "="*60)
            print("ADB COMMAND ERROR")
            print("="*60)
            print("• ADB command failed to execute")
            print("• Check if ADB is installed and in PATH")
            print("• Verify STB IP address is correct")
            print(f"• Error details: {e.stderr.strip()}")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return None

    def f_disable_cec(self, device):
        """
        Disable CEC (Consumer Electronics Control) on STB to prevent interference during tests.
        Uses multiple methods for Android 14 compatibility.
        
        Args:
            device (str): Device identifier
        
        Returns:
            bool: True if any CEC disable method succeeded, False otherwise
        """
        try:
            self.f_log("Disabling CEC (Consumer Electronics Control) - Android 14 compatible...")
            success_count = 0
        
            # Method 1: Traditional global settings (Android 13 and below)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "global", 
                    "hdmi_control_enabled", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 1: Global HDMI control disabled")
                success_count += 1
            except:
                self.f_log("• Method 1: Global HDMI control - FAILED")
        
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "global", 
                    "hdmi_volume_use_cec", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 1: Global HDMI volume CEC disabled")
                success_count += 1
            except:
                self.f_log("• Method 1: Global HDMI volume CEC - FAILED")
        
            # Method 2: Secure settings (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "secure", 
                    "hdmi_control_enabled", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 2: Secure HDMI control disabled")
                success_count += 1
            except:
                self.f_log("• Method 2: Secure HDMI control - FAILED")
        
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "secure", 
                    "hdmi_volume_use_cec", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 2: Secure HDMI volume CEC disabled")
                success_count += 1
            except:
                self.f_log("• Method 2: Secure HDMI volume CEC - FAILED")
        
            # Method 3: System settings (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "system", 
                    "hdmi_control_enabled", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 3: System HDMI control disabled")
                success_count += 1
            except:
                self.f_log("• Method 3: System HDMI control - FAILED")
        
            # Method 4: Direct property setting (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "setprop", "ro.hdmi.device_type", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 4: HDMI device type property disabled")
                success_count += 1
            except:
                self.f_log("• Method 4: HDMI device type property - FAILED")
        
            # Method 5: CEC service control (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "cmd", "hdmi_control", "cec_setting", "--enabled", "false"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 5: CEC service control disabled")
                success_count += 1
            except:
                self.f_log("• Method 5: CEC service control - FAILED")
        
            # Method 6: Alternative CEC disable (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "global", 
                    "hdmi_cec_enabled", "0"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 6: Alternative CEC setting disabled")
                success_count += 1
            except:
                self.f_log("• Method 6: Alternative CEC setting - FAILED")
        
            # Method 7: TV input service (Android 14)
            try:
                subprocess.run([
                    "adb", "-s", device, "shell", "settings", "put", "secure", 
                    "tv_input_hidden_inputs", "1"
                ], check=True, text=True, capture_output=True, timeout=10)
                self.f_log("• Method 7: TV input service configured")
                success_count += 1
            except:
                self.f_log("• Method 7: TV input service - FAILED")
        
            # Summary
            if success_count > 0:
                self.f_log(f"CEC disable completed: {success_count}/7 methods successful")
                self.f_log("• STB should now have reduced CEC interference")
                time.sleep(5)
                return True
            else:
                self.f_log("CEC disable failed: All methods unsuccessful")
                self.f_log("• Warning: CEC interference may occur during tests")
                self.f_log("• Tests will continue normally")
                time.sleep(5)
                return False
            
        except Exception as e:
            self.f_log(f"Critical error during CEC disable: {str(e)}")
            self.f_log("• Warning: CEC interference may occur during tests")
            self.f_log("• Tests will continue normally")
            time.sleep(5)
            return False

    def f_is_device_ready(self, device):
        """
        Check if device is ready to receive commands.
        
        Args:
            device (str): Device identifier
            
        Returns:
            bool: True if device is ready, False otherwise
        """
        try:
            result = subprocess.run(["adb", "-s", device, "get-state"], check=True, text=True, capture_output=True)
            return result.stdout.strip() == "device"
        except:
            return False

    def f_is_in_standby(self, device):
        """
        Detect if STB is in standby mode.
        
        Args:
            device (str): Device identifier
            
        Returns:
            bool: True if in standby, False otherwise
        """
        try:
            result = subprocess.run(["adb", "-s", device, "shell", "dumpsys", "power"], 
                                  text=True, capture_output=True, timeout=5)
            output = result.stdout.lower()
            return ("mwakefulness=asleep" in output or 
                   "mwakefulness=dozing" in output or 
                   "display power: state=off" in output)
        except:
            return False

    def f_wait_standby_exit(self, device, initial_time, duration):
        """
        Wait for STB to exit standby mode.
        
        Args:
            device (str): Device identifier
            initial_time (float): Test initial time
            duration (int): Maximum test duration
        """
        self.f_log("STB is in STANDBY. Waiting for wake-up...")
        while self.f_is_in_standby(device):
            if time.time() - initial_time >= duration:
                self.f_log(f"Maximum time of {duration} reached during standby.")
                sys.exit(0)
            time.sleep(10)
        self.f_log("STB returned from standby.")

    # ========================================================================
    # MAIN KEY SENDING
    # ========================================================================

    def f_send_key(self, device, key_code, key_name):
        """
        Send a virtual key to device via ADB.
        
        Args:
            device (str): Device identifier
            key_code (str): Android key code
            key_name (str): Descriptive key name for logs
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            subprocess.run(["adb", "-s", device, "shell", "input", "keyevent", key_code], 
                          check=True, text=True, capture_output=True, timeout=5)
            self.error_already_shown = False
            self.f_log(f"{key_name} sent successfully")
            return True
        except Exception as e:
            if not self.error_already_shown:
                self.f_log(f"Error sending {key_name}: {str(e)}")
                self.error_already_shown = True
            time.sleep(5)
            return False

    # ========================================================================
    # SPECIFIC KEYS - NAVIGATION
    # ========================================================================

    def f_send_home_key(self, device):
        """Send HOME key (code 3)"""
        if self.f_send_key(device, "3", "KEY_HOME"):
            time.sleep(10)
            return True
        return False

    def f_send_right_key(self, device):
        """Send RIGHT key (code 22)"""
        if self.f_send_key(device, "22", "KEY_RIGHT"):
            time.sleep(5)
            return True
        return False

    def f_send_left_key(self, device):
        """Send LEFT key (code 21)"""
        if self.f_send_key(device, "21", "KEY_LEFT"):
            time.sleep(5)
            return True
        return False

    def f_send_down_key(self, device):
        """Send DOWN key (code 20)"""
        if self.f_send_key(device, "20", "KEY_DOWN"):
            time.sleep(5)
            return True
        return False

    def f_send_up_key(self, device):
        """Send UP key (code 19)"""
        if self.f_send_key(device, "19", "KEY_UP"):
            time.sleep(5)
            return True
        return False

    def f_send_ok_key(self, device):
        """Send OK/SELECT key (code 23)"""
        if self.f_send_key(device, "23", "KEY_OK"):
            time.sleep(5)
            return True
        return False

    def f_send_back_key(self, device):
        """Send BACK key (code 4)"""
        time.sleep(10)
        return self.f_send_key(device, "4", "KEY_BACK")

    # ========================================================================
    # SPECIFIC KEYS - TV AND CHANNELS
    # ========================================================================

    def f_send_live_key(self, device):
        """Send LIVE key (code 170)"""
        if self.f_send_key(device, "170", "KEY_LIVE"):
            time.sleep(5)
            return True
        return False

    def f_send_guide_key(self, device):
        """Send GUIDE key (code 172)"""
        time.sleep(5)
        return self.f_send_key(device, "172", "KEY_GUIDE")

    def f_send_channelUP_key(self, device):
        """Send CHANNEL UP key (code 166) - with longer delay for zapping"""
        time.sleep(20)
        return self.f_send_key(device, "166", "KEY_CHANNEL_UP")

    def f_send_channelDOWN_key(self, device):
        """Send CHANNEL DOWN key (code 167) - with longer delay for zapping"""
        time.sleep(20)
        return self.f_send_key(device, "167", "KEY_CHANNEL_DOWN")

    # ========================================================================
    # SPECIFIC KEYS - VOLUME AND AUDIO
    # ========================================================================

    def f_send_volume_up_key(self, device):
        """Send VOLUME UP key (code 24)"""
        if self.f_send_key(device, "24", "KEY_VOLUME_UP"):
            time.sleep(3)
            return True
        return False

    def f_send_volume_down_key(self, device):
        """Send VOLUME DOWN key (code 25)"""
        if self.f_send_key(device, "25", "KEY_VOLUME_DOWN"):
            time.sleep(3)
            return True
        return False

    def f_send_mute_key(self, device):
        """Send MUTE key (code 164)"""
        if self.f_send_key(device, "164", "KEY_MUTE"):
            time.sleep(5)
            return True
        return False

    # ========================================================================
    # SPECIFIC KEYS - POWER
    # ========================================================================

    def f_send_standby_key(self, device):
        """Send standby command (code 26) - with 10s delay"""
        if self.f_send_key(device, "26", "KEY_STANDBY"):
            time.sleep(10)
            return True
        return False

    def f_send_wake_up_key(self, device):
        """Send wake-up command (code 224) - with 20s delay"""
        if self.f_send_key(device, "224", "KEY_WAKEUP"):
            time.sleep(20)
            return True
        return False

    # ========================================================================
    # APPLICATION OPENING
    # ========================================================================

    def f_send_flow_key(self, device):
        """
        Open default application via activity manager.
        """
        try:
            subprocess.run([
                "adb", "-s", device, "shell", "am", "start", "-n",
                "ar.com.flow.androidtv_stb/ar.com.flow.androidtv.base.view.BaseActivity",
                "-a", "android.intent.action.MAIN",
                "-c", "android.intent.category.LEANBACK_LAUNCHER"
            ], check=True, text=True, capture_output=True, timeout=5)
            self.f_log("KEY_APP sent successfully")
            time.sleep(15)
            return True
        except subprocess.SubprocessError as e:
            self.f_log(f"Error opening APP: {str(e)}")
            return False

    def f_open_app(self, device, package, description):
        """
        Open an application using monkey with LAUNCHER category.
        
        Args:
            device (str): Device identifier
            package (str): Application package name
            description (str): App description for logs
            
        Returns:
            bool: True if opened successfully, False otherwise
        """
        try:
            subprocess.run(
                ["adb", "-s", device, "shell", "monkey", "-p", package, 
                 "-c", "android.intent.category.LAUNCHER", "1"],
                check=True, text=True, capture_output=True, timeout=5
            )
            self.f_log(f"{description.strip()} opened successfully")
            time.sleep(30)
            return True
        except subprocess.SubprocessError as e:
            self.f_log(f"Error opening {description.strip()}: {str(e)}")
            return False

    def f_open_app_secondary(self, device, package, description):
        """
        Open an application using monkey with LEANBACK_LAUNCHER category.
        Used for apps that need this specific category.
        
        Args:
            device (str): Device identifier
            package (str): Application package name
            description (str): App description for logs
            
        Returns:
            bool: True if opened successfully, False otherwise
        """
        try:
            subprocess.run(
                ["adb", "-s", device, "shell", "monkey", "-p", package, 
                 "-c", "android.intent.category.LEANBACK_LAUNCHER", "1"],
                check=True, text=True, capture_output=True, timeout=5
            )
            self.f_log(f"{description} opened successfully")
            time.sleep(30)
            return True
        except subprocess.SubprocessError as e:
            self.f_log(f"Error opening {description}: {str(e)}")
            return False

    # ========================================================================
    # RECONNECTION SYSTEM
    # ========================================================================

    def f_reconnect_and_reinitialize(self, ip, port, initial_time, duration):
        """
        Standard reconnection system - tries to reconnect and reinitialize.
        
        Args:
            ip (str): STB IP
            port (int): ADB port
            initial_time (float): Test initial time
            duration (int): Maximum test duration
            
        Returns:
            tuple: (device identifier, boolean indicating if reconnected)
        """
        self.f_log("Attempting device reconnection...")
        while True:
            if time.time() - initial_time >= duration:
                self.f_log(f"Maximum execution time reached = {duration} during reconnection.")
                sys.exit(0)
            
            new_device = self.f_connect_device(ip, port)
            if new_device and self.f_is_device_ready(new_device):
                self.f_log("Reconnection successful! Restarting command sequence...")
                time.sleep(30)
                if self.f_send_home_key(new_device):
                    self.error_already_shown = False
                    return new_device, True
                else:
                    self.f_log("Failed to resend commands after reconnection.")
            else:
                self.f_log("Reconnection not yet possible. Trying again in 5s...")
                time.sleep(5)

    def f_reconnect_and_reinitialize_project1(self, ip, port, initial_time, duration):
        """
        Project 1 specific reconnection system.
        Reinitialize with GUIDE -> BACK sequence.
        
        Args:
            ip (str): STB IP
            port (int): ADB port
            initial_time (float): Test initial time
            duration (int): Maximum test duration
            
        Returns:
            tuple: (device identifier, boolean indicating if reconnected)
        """
        self.f_log("Attempting device reconnection (Project 1)...")
        while True:
            if time.time() - initial_time >= duration:
                self.f_log("Maximum execution time reached during reconnection.")
                sys.exit(0)
            
            new_device = self.f_connect_device(ip, port)
            if new_device and self.f_is_device_ready(new_device):
                self.f_log("Reconnection successful! Restarting Project 1 sequence...")
                time.sleep(30)
                if self.f_send_home_key(new_device):
                    self.f_send_guide_key(new_device)
                    self.f_send_back_key(new_device)
                    self.error_already_shown = False
                    return new_device, True
                else:
                    self.f_log("Failed to resend commands after reconnection.")
            else:
                self.f_log("Reconnection not yet possible. Trying again in 5s...")
            time.sleep(5)

    # ========================================================================
    # AUXILIARY FUNCTIONS
    # ========================================================================

    def f_check_and_send(self, func, device, ip, port, initial_time, duration):
        """
        Check standby and send command with failure handling.
        
        Args:
            func: Command function to execute
            device (str): Device identifier
            ip (str): STB IP
            port (int): ADB port
            initial_time (float): Test initial time
            duration (int): Maximum test duration
            
        Returns:
            tuple: (device identifier, boolean indicating if reconnected)
        """
        if self.f_is_in_standby(device):
            self.f_wait_standby_exit(device, initial_time, duration)
        
        if not func(device):
            return self.f_reconnect_and_reinitialize(ip, port, initial_time, duration)
        return device, False

    def f_check_and_send_project1(self, func, device, ip, port, initial_time, duration):
        """
        Check standby and send command with failure handling for Project 1 zapping.
        
        Args:
            func: Command function to execute
            device (str): Device identifier
            ip (str): STB IP
            port (int): ADB port
            initial_time (float): Test initial time
            duration (int): Maximum test duration
            
        Returns:
            tuple: (device identifier, boolean indicating if reconnected)
        """
        if self.f_is_in_standby(device):
            self.f_wait_standby_exit(device, initial_time, duration)
        
        if not func(device):
            return self.f_reconnect_and_reinitialize_project1(ip, port, initial_time, duration)
        return device, False

    def f_get_connection_info(self):
        """
        Get connection information from user via input.
        Shows list of connected devices before asking for IP.
        
        Returns:
            int: Test duration in seconds, or None if an error occurred.
        """
        try:
            self.f_list_connected_devices()
            
            self.ip = input("Enter the IP address (ex: 192.168.x.x): ").strip()
            if not self.ip:
                raise ValueError("IP address cannot be empty")
            
            self.port = 5555
            
            print("\n" + "="*60)
            print("SELECT THE DURATION OF THE TEST!")
            print("="*60)
            print("1 - 12 Hours")
            print("2 - 24 Hours")
            print("3 - Custom Duration")
            print("="*60)

            duration_input = input("\nEnter the desired duration: ").strip()

            if not duration_input:
                raise ValueError("Duration cannot be empty!")

            if duration_input == '1':
                duration = 12 * 60 * 60
                return duration
            
            elif duration_input == '2':
                duration = 24 * 60 * 60
                return duration
            
            elif duration_input == '3':
                custom_duration_input = input("\nSet the duration in seconds: ").strip()
                if not custom_duration_input:
                    raise ValueError("Custom duration cannot be empty!")
                try:
                    duration = int(custom_duration_input)

                    if duration <= 0:
                        raise ValueError("Duration must be a positive number")
                    
                    elif duration > 432000:
                        raise ValueError("Max duration of 120 hours / 5 days")
                except ValueError as ve:
                    if "invalid literal" in str(ve):
                        raise ValueError("Custom duration must be a valid positive integer")
                    raise
                return duration   
            else:
                raise ValueError("Invalid Option!")
            
        except ValueError as e:
            print("\n" + "="*60)
            print("INPUT ERROR")
            print("="*60)
            print(f"• {str(e)}")
            print("• Please enter valid values")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return None

    def f_initialize_device(self):
        """
        Initialize device connection and disable CEC.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        self.device = self.f_connect_device(self.ip, self.port)
        if not self.device or not self.f_is_device_ready(self.device):
            print("\n" + "="*60)
            print("CONNECTION ERROR")
            print("="*60)
            print("• Device is not ready")
            print("• Check ADB permission on STB")
            print("• Verify IP address and network connection")
            print("• Make sure STB is powered on")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return False
        
        self.f_disable_cec(self.device)
        return True

    # ========================================================================
    # PROJECT MENUS
    # ========================================================================

    def f_menu_project1(self):
        """Project 1 specific menu"""
        while True:
            print("\n" + "="*50)
            print("PROJECT 1 - AVAILABLE TESTS")
            print("="*50)
            print("1 - Zapping")
            print("2 - Navigation")
            print("3 - Apps")
            print("4 - StandbyWakeup")
            print("5 - Volume Control")
            print("0 - Back to main menu")
            print("="*50)
            
            try:
                option = input("Choose an option: ").strip()
                
                if option == "1":
                    self.f_test_zapping_project1()
                elif option == "2":
                    self.f_test_navigation_project1()
                elif option == "3":
                    self.f_test_apps()
                elif option == "4":
                    self.f_test_standby_wakeup()
                elif option == "5":
                    self.f_test_volume_control()
                elif option == "0":
                    break
                else:
                    print(" Invalid option! Choose a valid option.")
                    time.sleep(1)
                    os.system("cls" if os.name == "nt" else "clear")
                    
            except KeyboardInterrupt:
                print("\n Returning to main menu...")
                break
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(1)
                os.system("cls" if os.name == "nt" else "clear")

    def f_menu_project2(self):
        """Project 2 specific menu"""
        while True:
            print("\n" + "="*50)
            print("PROJECT 2 - AVAILABLE TESTS")
            print("="*50)
            print("1 - Zapping")
            print("2 - Navigation")
            print("3 - Apps")
            print("4 - StandbyWakeup")
            print("5 - Volume Control")
            print("0 - Back to main menu")
            print("="*50)
            
            try:
                option = input("Choose an option: ").strip()
                
                if option == "1":
                    self.f_test_zapping_standard()
                elif option == "2":
                    self.f_test_navigation_project2()
                elif option == "3":
                    self.f_test_apps()
                elif option == "4":
                    self.f_test_standby_wakeup()
                elif option == "5":
                    self.f_test_volume_control()
                elif option == "0":
                    break
                else:
                    print(" Invalid option! Choose a valid option.")
                    time.sleep(1)
                    os.system("cls" if os.name == "nt" else "clear")
                    
            except KeyboardInterrupt:
                print("\n Returning to main menu...")
                break
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(1)
                os.system("cls" if os.name == "nt" else "clear")

    def f_menu_project3(self):
        """Project 3 specific menu"""
        while True:
            print("\n" + "="*50)
            print("PROJECT 3 - AVAILABLE TESTS")
            print("="*50)
            print("1 - Zapping")
            print("2 - Navigation")
            print("3 - Apps")
            print("4 - StandbyWakeup")
            print("5 - Volume Control")
            print("0 - Back to main menu")
            print("="*50)
            
            try:
                option = input("Choose an option: ").strip()
                
                if option == "1":
                    self.f_test_zapping_standard()
                elif option == "2":
                    self.f_test_navigation_project3()
                elif option == "3":
                    self.f_test_apps()
                elif option == "4":
                    self.f_test_standby_wakeup()
                elif option == "5":
                    self.f_test_volume_control()
                elif option == "0":
                    break
                else:
                    print(" Invalid option! Choose a valid option.")
                    time.sleep(1)
                    os.system("cls" if os.name == "nt" else "clear")
                    
            except KeyboardInterrupt:
                print("\n Returning to main menu...")
                break
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(1)
                os.system("cls" if os.name == "nt" else "clear")

    # ========================================================================
    # ZAPPING TESTS
    # ========================================================================

    def f_test_zapping_standard(self):
        """
        Standard Zapping Test - Channel changing with default app.
        Sequence: HOME -> LIVE -> APP -> Channel UP/DOWN cycle
        """
        self.f_log("=== STARTING STANDARD ZAPPING TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("ZAPPING_STANDARD"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True

        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    time.sleep(5)
                    self.f_send_live_key(self.device)
                    time.sleep(5)
                    self.f_send_flow_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                           self.f_send_channelUP_key, self.f_send_channelUP_key, 
                           self.f_send_channelDOWN_key, self.f_send_channelUP_key, 
                           self.f_send_channelDOWN_key
                           ]:
                    
                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                                    self.port, initial_time, duration)
                    
                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")

        except Exception as e:
            self.f_log(f"Execution terminated by fatal error: {e}")
        
        self.f_log(f"Standard Zapping Test of {duration} seconds completed.")

    def f_test_zapping_project1(self):
        """
        Project 1 Zapping Test -
        Sequence: HOME -> GUIDE -> Channel UP/DOWN cycle
        """
        self.f_log("=== STARTING PROJECT 1 ZAPPING TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("ZAPPING_PROJECT1"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True

        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    time.sleep(5)
                    self.f_send_guide_key(self.device)
                    time.sleep(5)
                    self.f_send_ok_key(self.device)
                    time.sleep(5)
                    self.f_send_back_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                        self.f_send_channelUP_key, self.f_send_channelUP_key, 
                        self.f_send_channelDOWN_key, self.f_send_channelUP_key, 
                        self.f_send_channelDOWN_key
                        ]:
            
                    self.device, reconnected = self.f_check_and_send_project1(func, self.device, self.ip, 
                                            self.port, initial_time, duration)
                    
                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")

        except Exception as e:
            self.f_log(f"Execution terminated by fatal error: {e} (at loop {loop})")

        self.f_log(f"Project 1 Zapping Test of {duration} seconds completed.")

    # ========================================================================
    # NAVIGATION TESTS
    # ========================================================================

    def f_test_navigation_project2(self):
        """
        Project 2 Navigation Test
        Sequence: HOME -> Navigation
        """
        self.f_log("=== STARTING PROJECT 2 NAVIGATION TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("NAVIGATION_PROJECT2"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True
        
        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== INITIAL SEQUENCE: Ready to start navigation ===")
                    need_initial_sequence = False

                reconnected = False
                for func in [
                    self.f_send_home_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_up_key, self.f_send_up_key, self.f_send_up_key, self.f_send_up_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_ok_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_up_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_left_key, self.f_send_left_key,
                    self.f_send_up_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_up_key, self.f_send_left_key, self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key,
                ]:
                    
                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                                    self.port, initial_time, duration)
                    
                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")
                    
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Project 2 Navigation Test of {duration} seconds completed.")

    def f_test_navigation_project1(self):
        """
        Project 1 Navigation Test - Interface navigation sequence.
        """
        self.f_log("=== STARTING PROJECT 1 NAVIGATION TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("NAVIGATION_PROJECT1"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True

        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                    self.f_send_home_key, 
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_up_key, self.f_send_up_key, self.f_send_up_key, self.f_send_up_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_right_key,
                    self.f_send_up_key, self.f_send_left_key, self.f_send_home_key,
                    self.f_send_up_key, self.f_send_right_key, self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_up_key, self.f_send_up_key, self.f_send_up_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_home_key, self.f_send_up_key, self.f_send_right_key, self.f_send_right_key, self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_up_key, self.f_send_up_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_home_key
                    ]:

                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                                       self.port, initial_time, duration)

                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")
                    
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Project 1 Navigation Test of {duration} seconds completed.")

    def f_test_navigation_project3(self):
        """
        Project 3 Navigation Test - Interface navigation sequence.
        """
        self.f_log("=== STARTING PROJECT 3 NAVIGATION TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("NAVIGATION_PROJECT3"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True
        
        def send_flow_with_navigation(device):
            """Wrapper function to properly call flow_key in loop"""
            time.sleep(5)
            return self.f_send_flow_key(device)

        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                   self.f_send_home_key, self.f_send_home_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_home_key, self.f_send_up_key, self.f_send_right_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_home_key, self.f_send_up_key, self.f_send_right_key, self.f_send_right_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_home_key,
                    send_flow_with_navigation,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_down_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_back_key,
                    self.f_send_right_key, 
                    self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key,
                    self.f_send_down_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_up_key, self.f_send_up_key, self.f_send_up_key, self.f_send_up_key, self.f_send_up_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_back_key,
                    self.f_send_right_key, self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_back_key,
                    self.f_send_right_key, self.f_send_ok_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key, self.f_send_down_key, self.f_send_down_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_back_key, self.f_send_ok_key,
                    self.f_send_down_key, self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_down_key,
                    self.f_send_right_key, self.f_send_right_key, self.f_send_right_key,
                    self.f_send_back_key,
                    self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key, self.f_send_left_key,
                    self.f_send_ok_key
                ]:
                
                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                            self.port, initial_time, duration)

                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")
                    
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Project 3 Navigation Test of {duration} seconds completed.")

    # ========================================================================
    # APPS TEST
    # ========================================================================

    def f_test_apps(self):
        """
        Apps Test - Open and close apps
        Cycle: HOME -> App -> HOME -> Next App
        Apps tested: Netflix, Amazon Prime, YouTube, Disney+, Spotify, Max
        """
        self.f_log("=== STARTING APPS TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("APPS"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True
        
        def open_netflix(device):
            self.f_send_home_key(device)
            return self.f_open_app(device, "com.netflix.ninja", "Netflix")
        
        def open_amazon(device):
            self.f_send_home_key(device)
            return self.f_open_app_secondary(device, "com.amazon.amazonvideo.livingroom", "Amazon Prime")
        
        def open_youtube(device):
            self.f_send_home_key(device)
            return self.f_open_app(device, "com.google.android.youtube.tv", "YouTube")
        
        def open_disney(device):
            self.f_send_home_key(device)
            return self.f_open_app(device, "com.disney.disneyplus", "Disney+")
        
        def open_spotify(device):
            self.f_send_home_key(device)
            return self.f_open_app(device, "com.spotify.tv.android", "Spotify")
        
        def open_max(device):
            self.f_send_home_key(device)
            return self.f_open_app_secondary(device, "com.wbd.stream", "Max")
        
        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                    open_netflix, open_amazon, open_youtube, 
                    open_disney, open_spotify, open_max
                ]:
                
                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                                    self.port, initial_time, duration)
                    
                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")
            
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Apps Test of {duration} seconds completed.")

    # ========================================================================
    # VOLUME CONTROL TEST
    # ========================================================================

    def f_test_volume_control(self):
        """
        Volume Control Test - Tests volume up, down and mute functionality.
        Sequence: HOME -> VOL_UP x5 -> VOL_DOWN x5 -> MUTE -> MUTE -> Repeat
        Compatible with any Android STB device.
        """
        self.f_log("=== STARTING VOLUME CONTROL TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("• Use: screen -S [SessionName]")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("VOLUME_CONTROL"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True

        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== EXECUTING INITIAL SEQUENCE ===")
                    self.f_send_home_key(self.device)
                    need_initial_sequence = False
                    self.f_log("=== INITIAL SEQUENCE COMPLETED ===")
                
                reconnected = False
                for func in [
                    # Volume UP x5
                    self.f_send_volume_up_key, self.f_send_volume_up_key,
                    self.f_send_volume_up_key, self.f_send_volume_up_key,
                    self.f_send_volume_up_key,
                    # Volume DOWN x5
                    self.f_send_volume_down_key, self.f_send_volume_down_key,
                    self.f_send_volume_down_key, self.f_send_volume_down_key,
                    self.f_send_volume_down_key,
                    # MUTE toggle (on/off)
                    self.f_send_mute_key,
                    self.f_send_mute_key,
                    # Volume UP x3
                    self.f_send_volume_up_key, self.f_send_volume_up_key,
                    self.f_send_volume_up_key,
                    # Volume DOWN x3
                    self.f_send_volume_down_key, self.f_send_volume_down_key,
                    self.f_send_volume_down_key,
                    # MUTE toggle (on/off)
                    self.f_send_mute_key,
                    self.f_send_mute_key,
                ]:
                
                    self.device, reconnected = self.f_check_and_send(func, self.device, self.ip, 
                                                    self.port, initial_time, duration)
                    
                    if reconnected:
                        self.f_log("RECONNECTION DETECTED - RESTARTING TEST FROM BEGINNING")
                        loop = 0
                        need_initial_sequence = True
                        break
                
                if not reconnected:
                    loop += 1
                    self.f_log(f"LOOP {loop} CONCLUDED")
            
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Volume Control Test of {duration} seconds completed.")

    # ========================================================================
    # STANDBY/WAKEUP TEST
    # ========================================================================

    def f_test_standby_wakeup(self):
        """
        Standby/Wakeup Test - Standby and wake-up cycle.
        Sequence: STANDBY (10s delay) -> WAKEUP (20s delay) -> Repeat
        """
        self.f_log("=== STARTING STANDBY/WAKEUP TEST ===")
        
        if not os.getenv("STY"):
            print("\n" + "="*60)
            print("SCREEN SESSION REQUIRED")
            print("="*60)
            print("• This script must be executed within a 'screen' session")
            print("="*60)
            print("Returning to menu in 10 seconds...")
            print("="*60)
            time.sleep(10)
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        if not self.f_setup_logging("STANDBY_WAKEUP"):
            return
        duration = self.f_get_connection_info()
        
        if duration is None:
            return
        
        if not self.f_initialize_device():
            return
        
        initial_time = time.time()
        self.error_already_shown = False
        loop = 0
        need_initial_sequence = True
    
        try:
            while time.time() - initial_time < duration:
                
                if need_initial_sequence:
                    self.f_log("=== INITIAL SEQUENCE: Ready to start standby/wakeup cycle ===")
                    need_initial_sequence = False
                
                if not self.f_send_standby_key(self.device):
                    self.device, reconnected = self.f_reconnect_and_reinitialize(
                        self.ip, self.port, initial_time, duration)
                    loop = 0
                    need_initial_sequence = True
                    continue
                
                if not self.f_send_wake_up_key(self.device):
                    self.device, reconnected = self.f_reconnect_and_reinitialize(
                        self.ip, self.port, initial_time, duration)
                    loop = 0
                    need_initial_sequence = True
                    continue
                
                loop += 1
                self.f_log(f"LOOP {loop} CONCLUDED")
            
        except Exception as e:
            self.f_log(f"Execution terminated due to fatal error: {e}")
        
        self.f_log(f"Standby/Wakeup Test of {duration} seconds completed.")

# ============================================================================
# MAIN PROGRAM FUNCTIONS
# ============================================================================

def f_show_menu():
    if not os.getenv("STY"):
        print("\n This script MUST be executed within a 'screen' session")
        print("\n  Use: screen -S [SessionName]\n")
        sys.exit(1)
    
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "="*50)
    print("STB TEST SUITE - SELECT PROJECT")
    print("="*50)
    print("1 - Project 1")
    print("2 - Project 2")
    print("3 - Project 3")
    print("0 - Exit (quit)")
    print("="*50)

def f_main():
    """
    Main program function.
    Controls main menu and instantiates STBTester class.
    """
    tester = STBTester()
    
    while True:
        f_show_menu()
        try:
            option = input("Choose an option: ").strip()
            
            if option == "1":
                tester.f_menu_project1()
            elif option == "2":
                tester.f_menu_project2()
            elif option == "3":
                tester.f_menu_project3()
            elif option == "0":
                print("Closing STB Test Suite...")
                break
            else:
                print("Invalid option!!! Choose a valid option.")
                time.sleep(1)
                os.system("cls" if os.name == "nt" else "clear")
                
        except KeyboardInterrupt:
            print("\n\n Program interrupted by user.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    f_main()
