# %%
import subprocess
import time
from datetime import datetime, timedelta
import os
import shutil
from zipfile import ZipFile

def run_wireshark_session(interface, log_file_path, duration_minutes):
    # Generate a timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Construct the log file path
    log_file_path = os.path.join(log_file_path, f"wireshark_log_{timestamp}.pcap")

    # Construct the Wireshark command
    wireshark_command = [
        "C:\\Program Files\\Wireshark\\tshark.exe",
        "-i", interface,
        "-a", f"duration:{duration_minutes * 60}",  # Convert minutes to seconds
        "-w", log_file_path
    ]

    # Run Wireshark session
    subprocess.run(wireshark_command)

    return log_file_path

def zip_and_move_log(log_file_path, destination_folder):
    # Generate a timestamp for the zip file
    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Construct the zip file path
    zip_file_path = os.path.join(destination_folder, os.path.basename(log_file_path).replace(".pcap", ".zip"))

    # Zip the log file
    with ZipFile(zip_file_path, 'w') as zip_file:
        zip_file.write(log_file_path, os.path.basename(log_file_path))

    # Remove the original log file
    os.remove(log_file_path)

# %%
if __name__ == "__main__":
    # Replace 'your_interface' with the actual interface name of your GSM modem
    interface_name = "5"

    # temporary log file path
    log_file_path = "C:/Users/mkn/Documents/mkndaq/logs"
    
    # Specify the destination folder for the zip files
    destination_folder = "c:/users/mkn/Documents/mkndaq/staging/logs"

    # session duration
    duration_minutes = 10

    # Set the total duration to run the script (in seconds)
    total_duration = 6 * 60 * 60  # 6 hours

    # Record the start time
    start_time = datetime.now()

    # Run sessions every 20 minutes until the total duration is reached
    while (datetime.now() - start_time).total_seconds() < total_duration:
        # Get the current time
        current_time = datetime.now()

        # Start a new session every 10 minutes
        if current_time.minute % duration_minutes == 0:
            print(f"Starting Wireshark session at {current_time}")
            log_file_path = run_wireshark_session(interface_name, log_file_path, duration_minutes=duration_minutes)
            zip_and_move_log(log_file_path, destination_folder)

        # Sleep for a short duration before checking the time again
        time.sleep(60)

# %%