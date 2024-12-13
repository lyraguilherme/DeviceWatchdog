import sys
import os
import time
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from prettytable import PrettyTable

def ping_tester(ping_destination):
    try:
        # Use OS-native ping command
        if os.name == 'nt':
            # Windows
            command = ['ping', '-n', '3', '-w', '700', ping_destination]
        else:
            # Linux
            command = ['ping', '-c', '3', '-W', '700', ping_destination]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return "OK"
        else:
            return "FAIL"
    except Exception as e:
        return "FAIL"


def DeviceWatchdog(inventory):
    try:
        with open(inventory, "r") as f:
            devices_to_test = json.load(f)

        results_table = PrettyTable(['Host', 'Device IP', 'Ping Test', 'Test Time'])
        
        # Define the UTC timezone manually using datetime.timezone
        utc_zone = timezone.utc

        # Creating a ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor() as executor:
            while True:
                # Prepare to submit all ping tasks
                futures = []
                for device, values in devices_to_test.items():
                    device_ip = values["device_ip"]
                    futures.append(executor.submit(ping_tester, device_ip))

                # Get results once all tasks are completed
                results = [future.result() for future in futures]

                # Get the current time as timezone-aware datetime in UTC
                now = datetime.now(utc_zone)

                # Counts for status
                ok_count = results.count("OK")
                fail_count = results.count("FAIL")
                total_count = len(devices_to_test)

                # Add each result to the table
                for i, (device, values) in enumerate(devices_to_test.items()):
                    device_ip = values["device_ip"]
                    ping_result = results[i]
                    results_table.add_row([ 
                        device,
                        device_ip,
                        ping_result,
                        now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
                    ])

                # Clear the terminal and print the results
                os.system('cls' if os.name == 'nt' else 'clear')
                print(results_table)

                # Print the counts below the table
                print(f"\nResults OK      : {ok_count}")
                print(f"Results FAILED  : {fail_count}")
                print(f"Total tested    : {total_count}\n")
                
                # Clear the table for the next iteration
                results_table.clear_rows()

                # Wait for 30 seconds before running the next round of tests
                time.sleep(30)

    except KeyboardInterrupt:
        print('\nExiting script...')
    finally:
        print('Done.')

def main():
    inventory = sys.argv[1]
    DeviceWatchdog(inventory)

if __name__ == "__main__":
    main()
