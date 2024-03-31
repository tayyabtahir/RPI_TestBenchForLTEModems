import sys
import subprocess
import re
import time

def execute_command(command):
    """
    This method executes the command and captures the output

    Args:
        command (str): The command to execute.

    Returns:
        str: The output of the command.
    """

    # Use subprocess to execute the command and capture the output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()

    return output


def find_ip_address(text):
    """
    This method finds the IP address from response of "ifconfig <interface>"

    Args:
        text (str): The response of "ifconfig <interface>"

    Returns:
        str: The IP address.
    """

    # Regular expression pattern for an IP address
    patternfull = r"\binet \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    patternip = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

    # Search for the pattern
    match = re.search(patternfull, text)

    # If a match is found, return the IP address
    if match:
        match = re.search(patternip, match.group())
        return match.group()
    else:
        return None
        

def dialupTask(InstrumentData, DialupComport, messagesQueue):
    """
    This method is the main dialup task

    Args:
        None

    Returns:
        None
    """

    print("[DialUp-Task] Dialup Task Started")

    # Initiate the dialup connection
    print("[DialUp-Task]  Initiating Dialup Connection")
    response = execute_command("sudo pon MyProvider")
    print(response.decode())

    # Wait for three Seconds
    print("[DialUp-Task]  Waiting for 3 seconds")
    time.sleep(3)

    # Check if the connection is successful
    response = execute_command("plog")
    print(response.decode())
    match = re.search(r"Connection terminated", response.decode())
    if match:
        print("[DialUp-Task]  Dialup Connection Failed")
        return
    else:
        print("[DialUp-Task]  Dialup Connection Successful")

    # Check PPP connection in the system
    response = execute_command("ifconfig")
    print(response.decode())
    match = re.search(r"ppp0", response.decode())
    if match:
        print("[DialUp-Task]  PPP Connection Successful")
    else:
        print("[DialUp-Task]  PPP Connection Failed")

    # Check the IP address
    response = execute_command("ifconfig ppp0")
    print(response.decode())
    ip_address = find_ip_address(response.decode())
    print(f"[DialUp-Task]  IP Address: {ip_address}")

    # Add static route for iperf server
    print("[DialUp-Task]  Adding static route for iperf server")
    print(f"[DialUp-Task]  sudo ip route add 209.58.159.68/32 via {ip_address}")
    response = execute_command(f"sudo ip route add 209.58.159.68/32 via {ip_address}")
    print(response.decode())

    # Check the route
    print("[DialUp-Task]  Checking the route")
    response = execute_command("ip route")
    print(response.decode())

    counter = 0
    while True:
        InstrumentData["Running_Task"] = "Running iperf data transfer"
        
        # Execute iperf client for 60 seconds
        print("[DialUp-Task]  Executing iperf client for 600 seconds")
        response = execute_command("iperf3 -c 209.58.159.68 -p 5201-5210 -t 600secs")
        print(response.decode())
        counter += 1

        if response:
            # Parse the iperf results
            lines = response.decode().splitlines()
            colomns = lines[-3].split()
            print(f"[DialUp-Task] Transfer Rate: {colomns[6]} {colomns[7]}")

            # Update the Instrument Data for display
            InstrumentData["Running_Task"] = "Test Completed"
            InstrumentData["Final_Result"] = f"{colomns[6]} {colomns[7]}" 
            break
        else:
            # wait for 5 seconds before retrying
            time.sleep(5)

        if counter > 5:
            print("[DialUp-Task]  Failed to get iperf results")
            messagesQueue['Display'].put("iperf Connection Failed")
            break

    # Terminate the dialup connection
    print("[DialUp-Task]  Terminating Dialup Connection")
    response = execute_command("sudo poff MyProvider")
    print(response.decode())

    print("[DialUp-Task]  Dialup Task Completed")
    return