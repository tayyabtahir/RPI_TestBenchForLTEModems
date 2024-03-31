import json
import re
import threading
import time
import queue
import boto3
import json
from serialCOM.serial_communication import SerialCommunication
from serialCOM.dut_communication import handle_dut_commands
from DataCommunication.dataOverDialup import dialupTask
from Display.LcdLib import DisplayTask
ATComport = '/dev/ttyUSB2'
DialupComport = '/dev/ttyUSB3'

InstrumentData = {}
messagesQueue = {
}

messagesQueue['Dialup'] = queue.Queue()
messagesQueue['Display'] = queue.Queue()

def handle_serial_display():
    """
    Function to handle serial display.
    """
    displayQueue = messagesQueue['Display']

    DisplayTask(InstrumentData, displayQueue)
    return

def handle_dialup_commands():
    """
    Thread will setup the dial and run iperf data transfer
    """
    dialupQueue = messagesQueue['Dialup']

    # wait for module to be ready
    event = dialupQueue.get()
    if event == '[AT] start':
        print('[Main] Module registered. Starting dialup in 5 seconds')
        InstrumentData["Running_Task"] = "Starting Dialup"
        time.sleep(5)
        dialupTask(InstrumentData, DialupComport, messagesQueue)
    return

def handle_at_commands():
    """
    Function will communicate with DUT over AT interface
    After initialization sequence it will keep on monitoring
    the registeration state of the device and will keep signal quality
    in check as well
    """
    # wait for 90 seconds for module USB interface to be ready on reboot
    time.sleep(90)
    handle_dut_commands(InstrumentData, ATComport, messagesQueue)
    return

def write_to_s3(output_data, bucket_name, file_name):
    """
    Function to write the output data to an S3 bucket.

    Args:
        output_data (dict): The output data to write.
        bucket_name (str): The name of the S3 bucket.
        file_name (str): The name of the file to write.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    # Create a session using your AWS credentials
    s3 = boto3.resource(
        's3',
        aws_access_key_id='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        region_name='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    )

    # Convert the output_data to JSON
    output_json = json.dumps(output_data)

    try:
        # Write the JSON data to the S3 bucket
        s3.Object(bucket_name, file_name).put(Body=output_json)
        return "Success: Data written to S3 bucket."
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage:
if __name__ == "__main__":

    InstrumentData["Running_Task"] = "Getting Started"

    # Create threads for handling AT and dial-up commands
    at_thread = threading.Thread(target=handle_at_commands)
    display_thread = threading.Thread(target=handle_serial_display)
    dialup_thread = threading.Thread(target=handle_dialup_commands)
    InstrumentData["CloseAllThread"] = "no"
    
    # Start the threads
    display_thread.start()
    at_thread.start()
    dialup_thread.start()
    
    
    # Join the threads to wait for their completion
    dialup_thread.join()
    InstrumentData["CloseAllThread"] = "yes"
    at_thread.join()
    display_thread.join()
    print("All threads are stopped")

    # create output json data

    output_data = {
        "SIM ICCID": InstrumentData["iccid"],
        "SIM IMSI": InstrumentData["imsi"],
        "FW Version": InstrumentData["cgmr"],
        "IMEI": InstrumentData["imei"],
        "Signal Quality": InstrumentData["csq_rssi"],
        "Network": InstrumentData["cops_oper"],
        "Network Tracking Area": InstrumentData["Current_Tac"],
        "Network Cell ID": InstrumentData["Current_Ci"],
        "Test Time": InstrumentData["cclk"],
        "Throughput": InstrumentData["Final_Result"],
        "Out of Coverage Count": InstrumentData["OOC_count"],
    }

    print(json.dumps(output_data, indent=4))

    outputTime = output_data["Test Time"].strip('"\r')
    # Replace the slashes and comma with nothing, and the hyphen with an underscore
    formatted_time = outputTime.replace('/', '').replace(',', '_').replace('-', '_').replace(':', '').replace('+', '_')
    simICCId = output_data["SIM ICCID"]
    fileName = f"{simICCId}_{formatted_time}.json"

    ret = write_to_s3(output_data, 'lte-performance-results', fileName)
    print(ret)  # Output: Success: Data written to S3 bucket.
