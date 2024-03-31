import serial
import time
from datetime import datetime
    
class SerialCommunication:
    """
    A class for handling serial communication.

    Args:
        serial_port (str): The serial port to connect to. Defaults to '/dev/ttyUSB0'.
        baud_rate (int): The baud rate for the serial connection. Defaults to 115200.
        enable_logging (bool): Whether to enable logging. Defaults to True.

    Attributes:
        serial_port (str): The serial port to connect to.
        baud_rate (int): The baud rate for the serial connection.
        ser: The serial port object.
        enable_logging (bool): Whether logging is enabled.
    """
    def __init__(self, serial_port='/dev/ttyUSB2', baud_rate=115200, enable_logging=True, timeout=5):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.ser = None
        self.enable_logging = enable_logging
        # Open the serial connection upon request
        self.open_connection(timeout)
    
    
    def open_connection(self, timeout=5):
        """
        Opens the serial connection.

        Args:
            timeout (float): The timeout for opening the serial connection. Defaults to 5 seconds.

        Returns:
            int: An error code. 0 if successful, -1 otherwise.
        """
        error_code = -1
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=timeout)
            if self.ser.is_open:
                if self.enable_logging:
                    print(f"Connected to {self.serial_port} at {self.baud_rate} baud")
                    error_code = 0
            else:
                if self.enable_logging:
                    print("Failed to open serial port.")
        except serial.SerialException as e:
            if self.enable_logging:
                print(f"Serial port error: {e}")
        return error_code
        
        
    def close_connection(self):
        """
        Closes the serial connection.
        """
        if self.ser and self.ser.is_open:
            self.ser.close()
            if self.enable_logging:
                print("Serial port closed.")
                
        else:
            print("[ERROR] Serial port already closed.")
       
          
    def read_response(self, timeout=1):
        """
        Reads response from the serial port.

        Args:
            timeout (float): The timeout for reading the response. Defaults to 1 second.

        Returns:
            str: The response read from the serial port.
        """
        response = ""
        start_time = time.time()
        if (self.ser != None):
            while time.time() - start_time < timeout:
                response += self.ser.readline().decode()
        else:
            print("[ERROR] Serial port error")
        return response
    
    def send_command_and_read_response(self, command, response, timeout=5):
        """
        Sends a command and reads the response from the serial port.

        Args:
            command (str): The command to send.
            response (str): The response to store the read response.
            timeout (float): The timeout for sending the command and reading the response. Defaults to 1 second.

        Returns:
            int: An error code. 0 if successful, -1 otherwise.
            str: The response to store the read response
        """
        error_code = -1
        try:
            if self.ser and self.ser.is_open:
                if self.enable_logging:
                    print(self.get_formatted_time(), command)
                self.ser.write(command.encode())               
                
                # Wait for response
                response = ''
                start_time = time.time()
                while (time.time() - start_time < timeout):
                    response += self.ser.readline().decode()
                    if "OK" in response:
                        break

                
                if self.enable_logging:
                    print(self.get_formatted_time(), response)          
                error_code = 0
        except serial.SerialException as e:
            if self.enable_logging:
                print(f"Serial port error: {e}")
        
        return error_code,response
                
    def send_command_and_wait_for_string(self, command, response, expected_response=None, timeout=1):
        """
        Sends a command and waits for a specific string.

        Args:
            command (str): The command to send.
            response (str): The response to store the read response.
            expected_response (str): The expected response. If provided, the method will return 0 only if the expected response is received.
            timeout (float): The timeout for sending the command and waiting for the response. Defaults to 1 second.

        Returns:
            int: An error code. 0 if successful, -1 otherwise.
            str: The response to store the read response
        """
        error_code = -1
        try:
            if self.ser and self.ser.is_open:
                if self.enable_logging:
                    print(self.get_formatted_time(), command)
                self.ser.write(command.encode())
                response = self.read_response(timeout)
                if self.enable_logging:
                    print(self.get_formatted_time(), response)
                if expected_response is not None:
                    if expected_response in response:
                        error_code = 0
        except serial.SerialException as e:
            if self.enable_logging:
                print(f"Serial port error: {e}")
        
        return error_code,response
    

    def receive_urc(self, timeout=5):
        """
        Receive Unsolicited Result Codes (URCs) ending with \r\n from the serial port.

        Args:
            serial_port (serial.Serial): The serial port object.

        Returns:
            str: The received URC.
        """
        urc = ""
        response = ""
        # wait 10 seconds for the URC
        start_time = time.time()
        while time.time() - start_time < 10:
            response = self.read_response(timeout)
            if response.endswith('\r\n'):
                urc += response
                break
            else:
                urc += response

        if self.enable_logging:
            print(self.get_formatted_time(), urc)       
            
        return urc


    def get_formatted_time(self):
        """
        Get the current system time in the format [hh:mm:ss ms].

        Returns:
            str: The formatted time string.
        """
        current_time = datetime.now()
        formatted_time = current_time.strftime("[%H:%M:%S %f]")
        return formatted_time