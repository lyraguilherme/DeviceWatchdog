import sys
import os
import time
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime, timezone
from prettytable import PrettyTable

def ping_tester(ping_destination, pingq):
    try:
        # Use OS-native ping command
        if os.name == 'nt':
            # Windows
            command = ['ping', '-n', '1', '-w', '500', ping_destination]
        else:
            # Linux
            command = ['ping', '-c', '1', '-W', '500', ping_destination]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            pingq.put("OK")
        else:
            pingq.put("FAIL")
    except Exception as e:
        pingq.put("FAIL")


def DeviceWatchdog(inventory):
    try:
        with open(inventory, "r") as f:
            devices_to_test = json.load(f)

        results_table = PrettyTable(['Host', 'Device IP', 'Ping Test', 'Test Time'])
        pingq = Queue()

        # Define the UTC timezone manually using datetime.timezone
        utc_zone = timezone.utc  # This is equivalent to timezone(timedelta(hours=0))

        with ThreadPoolExecutor() as executor:
            while True:
                for device, values in devices_to_test.items():
                    device_ip = values["device_ip"]
                    
                    ping_future = executor.submit(ping_tester, device_ip, pingq)
                    
                    pingstatus = ping_future.result()
                    
                    # Get the current time as timezone-aware datetime in UTC
                    now = datetime.now(utc_zone)
                    results_table.add_row([ 
                        device,
                        device_ip,
                        pingq.get(),
                        now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
                    ])

                os.system('cls' if os.name == 'nt' else 'clear')
                print(results_table)
                results_table.clear_rows()

                time.sleep(3)

    except KeyboardInterrupt:
        print('\nExiting script...')
    finally:
        print('Done.')

def main():
    inventory = sys.argv[1]
    DeviceWatchdog(inventory)

if __name__ == "__main__":
    main()
