import sys
import os
import time
import subprocess
import itertools
import json
import threading
from netmiko import ConnectHandler, NetMikoAuthenticationException, NetMikoTimeoutException
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime
from prettytable import PrettyTable

stop_animation = False

def animated_progress():
    global stop_animation
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if stop_animation:
            break
        print(f'\r[{c}] Running tests... use CTRL+C to stop.', end='')
        time.sleep(0.1)
    print('\r', end='')

def ping_tester(ping_destination, pingq):
    try:
        # Use OS-native ping command
        if os.name == 'nt':
            # Windows
            command = ['ping', '-n', '1', '-w', '1000', ping_destination]
        else:
            # Unix-based systems
            command = ['ping', '-c', '1', '-W', '1', ping_destination]
        
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            pingq.put("OK")
        else:
            pingq.put("FAIL")
    except Exception as e:
        pingq.put("FAIL")

def ssh_tester(device_ip, ssh_user, ssh_pass, sshq, device_type='cisco_ios'):
    device = {
        'device_type': device_type,
        'ip': device_ip,
        'username': ssh_user,
        'password': ssh_pass,
    }
    
    try:
        connection = ConnectHandler(**device)
        sshq.put("OK")
        connection.disconnect()
    except NetMikoAuthenticationException:
        sshq.put("Authentication Exception")
    except NetMikoTimeoutException:
        sshq.put("Connection Timeout")
    except Exception as e:
        sshq.put(f"SSH Exception: {e}")

def DeviceWatchdog():
    global stop_animation
    try:
        with open("odonto.json", "r") as f:
            devices_to_test = json.load(f)

        results_table = PrettyTable(['Host', 'Device IP', 'Ping Test', 'SSH Test', 'Time (UTC)'])
        pingq = Queue()
        sshq = Queue()

        with ThreadPoolExecutor() as executor:
            # Start animation in a separate thread
            t = threading.Thread(target=animated_progress)
            t.start()

            while True:
                for device, values in devices_to_test.items():
                    device_ip = values["device_ip"]
                    ssh_user = values["username"]
                    ssh_pass = values["password"]
                    
                    ping_future = executor.submit(ping_tester, device_ip, pingq)
                    ssh_future = executor.submit(ssh_tester, device_ip, ssh_user, ssh_pass, sshq)
                    
                    pingstatus = ping_future.result()
                    sshstatus = ssh_future.result()
                    
                    now = datetime.utcnow()
                    results_table.add_row([device, device_ip, pingq.get(), sshq.get(), now.strftime("%Y-%m-%d %H:%M:%S")])

                os.system('cls' if os.name == 'nt' else 'clear')
                print(results_table)
                results_table.clear_rows()

                time.sleep(3)

    except KeyboardInterrupt:
        stop_animation = True
        print('\nExiting script...')
    finally:
        print('Done.')

def main():
    DeviceWatchdog()

if __name__ == "__main__":
    main()
