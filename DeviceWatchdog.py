import sys
import os
import time
import ping3
import subprocess
import itertools
import curses
import paramiko
import json
import threading
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
        print(f'\r[{c}] Running tests... ', end='')
        time.sleep(0.1)

def ping_tester(ping_destination, pingq):
    try:
        # use the ping() function from ping3 library
        response_time = ping3.ping(ping_destination, timeout=1)
        if response_time is not None:
            pingq.put("OK")
        else:
            pingq.put("FAIL")
    except Exception as e:
        pingq.put("FAIL")

def ssh_tester(device_ip, ssh_user, ssh_pass, sshq):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(device_ip, username=ssh_user, password=ssh_pass, timeout=1)
        sshq.put("OK")
    except paramiko.ssh_exception.AuthenticationException:
        sshq.put("Authentication Exception")
    except paramiko.ssh_exception.NoValidConnectionsError:
        sshq.put("Connection Timeout")
    except paramiko.ssh_exception.SSHException:
        sshq.put("SSH Exception")
    except Exception as unknown_error:
        sshq.put("Unknown Error")
    finally:
        client.close()

def DeviceWatchdog():
    global stop_animation
    try: 
        # reads the JSON file
        with open("my_devices.json", "r") as f:
            devices_to_test = json.load(f)
        f.close()        

        # defines the 'results_table' headers
        results_table = PrettyTable(['Hostname(JSON)', 'Device IP', 'Ping Test', 'SSH Test', 'Timestamp'])
        pingq = Queue()
        sshq = Queue()

        # create an instance of ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            while True:
                print('\n[#] Script will run continuously. Use CTRL+C to exit.')

                # starts animation
                t = threading.Thread(target=animated_progress)
                t.start()

                # runs connectivity tests
                for device, values in devices_to_test.items():
                    device_ip = values["device_ip"]
                    ssh_user = values["username"]
                    ssh_pass = values["password"]
                    
                    # submit the ping and ssh tester funcions using threading
                    ping_future = executor.submit(ping_tester, device_ip, pingq)
                    ssh_future = executor.submit(ssh_tester, device_ip, ssh_user, ssh_pass, sshq)
                    
                    # wait for all threads to complete
                    ping_future.result()
                    ssh_future.result()
                    pingstatus = pingq.get()
                    sshstatus = sshq.get()
                    now = datetime.now()
                    
                    # adds test results from each device as a row on 'results_table'
                    results_table.add_row([device, device_ip, pingstatus, sshstatus, now.strftime("%Y-%m-%d %H:%M:%S")])

                time.sleep(3)
                os.system('cls' if os.name == 'nt' else 'clear')
                print(results_table)
                results_table.clear_rows()
            executor.shutdown()

    except KeyboardInterrupt:
        stop_animation = True
        print('\nExiting script...')
    finally:
        print('Done.')

def main():
    DeviceWatchdog()

if __name__ == "__main__":
    main()
