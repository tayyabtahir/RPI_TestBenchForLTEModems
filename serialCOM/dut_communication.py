import re
import json
import time
from serialCOM.serial_communication import SerialCommunication

Module = "[DUT_COMM]"

def handle_dut_commands(InstrumentData, ATComport, messagesQueue, baud_rate=921600, timeout=5, enable_logging=True):

    # Entries for internal states
    InstrumentData["Current_Reg_Stat"] = -1
    InstrumentData["Current_Reg_Cell"] = -1
    InstrumentData["Current_Tac"] = None
    InstrumentData["Current_Ci"] = None
    InstrumentData["Running_Task"] = "Initialising DUT"
    InstrumentData["OOC_count"] = 0
    
    """
    Function to handle AT commands.
    """
    ser_comm_obj = SerialCommunication(serial_port=ATComport, baud_rate=baud_rate, timeout=timeout, enable_logging=enable_logging)

    response = ""

    # Verify serial connection with 5 AT commands
    for i in range(5):
        ATChannelWorking = 0
        errorCode,response = ser_comm_obj.send_command_and_read_response("AT\r\n", response)
        print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

        match = re.search(r"OK", response)
        if match:
            ATChannelWorking = 1
            break
    
    # If AT Channel is not working, exit the thread
    if not ATChannelWorking:
        print(f"[DUT_COMM] AT Channel not working. Exiting DUT thread")
        messagesQueue['Display'].put("AT Channel not working")
        return
    
    #-----------------------------------------------
    # This command sets module to Full functionality
    #-----------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CFUN=1\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None
    
    match = re.search(r"OK", response)
    InstrumentData["cfun_val"] = 1 if match else None
    
    
    #--------------------------------
    # This command sets Echo mode OFF
    #--------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("ATE0\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None
    
    match = re.search(r"OK", response)
    InstrumentData["ate_val"] = 0 if match else 1
    
    
    #-------------------------------------------------------
    # This command controls the format of error result codes
    #-------------------------------------------------------
    
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CMEE=2\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None
    
    match = re.search(r"OK", response)
    InstrumentData["cmee_val"] = 2 if match else 0

    
    #----------------------------------------------------------------------------------------
    # This command enters a password or queries whether or not the module requires a password 
    #-------------------------------------------------------------------------st---------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CPIN?\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None
    
    match = re.search(r"\+CPIN: READY", response)
    InstrumentData["cpin_stat"] = 1 if match else None

    
    #--------------------------------------------------------------------------
    # This command requests the International Mobile Subscriber Identity (IMSI)
    #--------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CIMI\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"(\d+)", response)
    InstrumentData["imsi"] = str(match.group(1)) if match else None

    
    #-------------------------------------------------------------------------------------------
    # This command returns the ICCID (Integrated Circuit Card Identifier) number of (U)SIM card.
    #-------------------------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+QCCID\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"\+QCCID: (\d+)", response)
    InstrumentData["iccid"] = str(match.group(1)) if match else None

    
    #------------------------------------------------------------------------------------------
    # This Execution command requests the International Mobile Equipment Identity (IMEI) number
    #------------------------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CGSN\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"(\d+)", response)
    InstrumentData["imei"] = str(match.group(1)) if match else None

    
    #-------------------------------------------------------------------------------
    # This Execution command delivers the identification text of MT firmware version
    #-------------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CGMR\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"(.+)[\r\n]+?OK", response)
    InstrumentData["cgmr"] = str(match.group(1)) if match else None

    
    #-------------------------------------------------------------------------------------------------
    # This command indicates the received signal strength <rssi> and the channel bit error rate <ber>.
    #-------------------------------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CSQ\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"\+CSQ: (\d+),(\d+)", response)
    InstrumentData["csq_rssi"] = int(match.group(1)) if match else 199
    InstrumentData["csq_ber"] = int(match.group(2)) if match else 99

    #-------------------------------------------------------------
    # This command enables URC for the network registration status
    #-------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_wait_for_string("AT+CEREG=2\r\n", response, expected_response="OK")
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    # wait 120 seconds for the modem to register
    start_time = time.time()
    InstrumentData["Running_Task"] = "Waiting for Network Registration"

    while time.time() - start_time < 120:
        #--------------------------------------------------------------
        # This command queries the real time clock (RTC) of the module.
        #--------------------------------------------------------------
        errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CEREG?\r\n", response)
        print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

        # If modem is registered
        match = re.search(r"\+CEREG: (\d),(\d+),(.+),(.+),(\d+)", response)
        if match:
            InstrumentData["cereg_stat"] = int(match.group(2)) if match else -1
            InstrumentData["cereg_tac"] = str(match.group(3)) if match else None
            InstrumentData["cereg_ci"] = str(match.group(4)) if match else None
            InstrumentData["cereg_act"] = int(match.group(5)) if match else -1

        else:
            # If modem is not registered
            match = re.search(r"\+CEREG: \d,(\d)", response)
            if match:
                InstrumentData["cereg_stat"] = int(match.group(1)) if match else -1
                InstrumentData["cereg_tac"] = None
                InstrumentData["cereg_ci"] = None
                InstrumentData["cereg_act"] = -1

        # Write vals in registeration stat
        InstrumentData["Current_Reg_Stat"] = InstrumentData["cereg_stat"]
        # Write vals in registeration cell
        InstrumentData["Current_Reg_Cell"] = InstrumentData["cereg_act"]
        # Write vals in tracking area code
        InstrumentData["Current_Tac"] = InstrumentData["cereg_tac"]
        # Write vals in cell ID
        InstrumentData["Current_Ci"] = InstrumentData["cereg_ci"]
        
        # If modem is registered, break the loop
        if InstrumentData["Current_Reg_Stat"] == 1 or InstrumentData["Current_Reg_Stat"] == 5:
            print(f"[DUT_COMM] Sending start event to Dialup thread")
            messagesQueue['Dialup'].put("[AT] start")
            break

    
    if InstrumentData["Current_Reg_Stat"] != 1 and InstrumentData["Current_Reg_Stat"] != 5:
        print(f"[DUT_COMM] Modem not registered. Exiting DUT thread")
        messagesQueue['Display'].put("Unable to register with Network")
        return

    
    #-------------------------------------------------------------------------------------------------------------
    # This command returns the current operators and their status, and allows setting automatic network selection.
    #-------------------------------------------------------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+COPS?\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"\+COPS: (\d+),(\d+),(.+),(\d+)", response)
    InstrumentData["cops_mode"] = int(match.group(1)) if match else None
    InstrumentData["cops_oper_format"] = int(match.group(2)) if match else None
    InstrumentData["cops_oper"] = str(match.group(3)) if match else None
    InstrumentData["cops_act"] = str(match.group(4)) if match else None

    
    #--------------------------------------------------------------
    # This command queries the real time clock (RTC) of the module.
    #--------------------------------------------------------------
    errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CCLK?\r\n", response)
    print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

    match = re.search(r"\+CCLK: (.+)", response)
    InstrumentData["cclk"] = str(match.group(1)) if match else None

    # Convert the JSON object to a string
    json_str = json.dumps(InstrumentData, indent=4)  # The 'indent' parameter adds indentation for better readability
    # Print the JSON string
    print("[DUT_COMM] InstrumentData: " + json_str)

    print(f"------------------------------------")
    print(f"\tStart URC Monitoring")
    print(f"------------------------------------")

    #---------------
    # Run the thread
    #---------------
    while InstrumentData["CloseAllThread"] != "yes":
    
        response = ser_comm_obj.receive_urc()
        if response == "":
            continue

        ChangeDetected = 0

        #------------------
        # Process CEREG URC
        #------------------

        # If modem is registered
        match = re.search(r"\+CEREG: (\d+),(.+),(.+),(\d+)", response)
        if match:
            InstrumentData["cereg_stat"] = int(match.group(1)) if match else -1
            InstrumentData["cereg_tac"] = str(match.group(2)) if match else None
            InstrumentData["cereg_ci"] = str(match.group(3)) if match else None
            InstrumentData["cereg_act"] = int(match.group(4)) if match else -1

        else:
            # If modem is not registered
            match = re.search(r"\+CEREG: \d,([0234])", response)
            if match:
                InstrumentData["cereg_stat"] = int(match.group(1)) if match else -1
                InstrumentData["cereg_tac"] = None
                InstrumentData["cereg_ci"] = None
                InstrumentData["cereg_act"] = -1

        #-----------------------------
        # Process Registeration Events
        #-----------------------------
        if InstrumentData["Current_Reg_Stat"] != InstrumentData["cereg_stat"]:
            # Create Event for change in registeration stat
            InstrumentData["Current_Reg_Stat"] = InstrumentData["cereg_stat"]
            ChangeDetected = 1

            if InstrumentData["cereg_stat"] == 0 or InstrumentData["cereg_stat"] == 2 or InstrumentData["cereg_stat"] == 3 or InstrumentData["cereg_stat"] == 4:
                InstrumentData["OOC_count"] += 1

        if InstrumentData["Current_Reg_Cell"] != InstrumentData["cereg_act"]:
            # Create Event for change in registeration cell
            InstrumentData["Current_Reg_Cell"] = InstrumentData["cereg_act"]
            ChangeDetected = 1

        if InstrumentData["Current_Tac"] != InstrumentData["cereg_tac"]:
            # Create Event for change in tracking area code
            InstrumentData["Current_Tac"] = InstrumentData["cereg_tac"]
            ChangeDetected = 1

        if InstrumentData["Current_Ci"] != InstrumentData["cereg_ci"]:
            # Create Event for change in cell ID
            InstrumentData["Current_Ci"] = InstrumentData["cereg_ci"]
            ChangeDetected = 1

        if ChangeDetected:
            #-------------------------------------------------------------------------------------------------
            # This command indicates the received signal strength <rssi> and the channel bit error rate <ber>.
            #-------------------------------------------------------------------------------------------------
            errorCode,response = ser_comm_obj.send_command_and_read_response("AT+CSQ\r\n", response)
            print(f"[DUT_COMM] error {errorCode}") if errorCode != 0 else None

            match = re.search(r"\+CSQ: (\d+),(\d+)", response)
            InstrumentData["csq_rssi"] = int(match.group(1)) if match else 199
            InstrumentData["csq_ber"] = int(match.group(2)) if match else 99

            #-------------------------------------------------------------------------------------------------
            # Create Event for display.
            #-------------------------------------------------------------------------------------------------
            # Selective list of keys to print
            selected_keys = ["Current_Reg_Stat", "Current_Reg_Cell", "Current_Tac", "Current_Ci", "csq_rssi", "csq_ber"]
            # Create a new dictionary containing only the selected keys
            selected_data = {key: value for key, value in InstrumentData.items() if key in selected_keys}
            # Convert the selected data to JSON string
            json_str = json.dumps(selected_data, indent=4)
            # Print the JSON string
            print("[DUT_COMM] InstrumentData: " + json_str)

    # Optionally, you can close the connection explicitly
    ser_comm_obj.close_connection()
    print(f"[DUT_COMM] Connection closed")
    print(f"[DUT_COMM] Exiting DUT thread")
    return
