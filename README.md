# RPI_TestBenchForLTEModems
Test any LTE modems for its Upload/Download speeds for the operator you are working with.


# Raspberry Pi LTE Network Performance Testing Application

This Python application is designed to test the network performance of a LTE module connected to a Raspberry Pi. It performs the following tasks:

1. **Initialization and Registration of Quectel LTE Module**:
   - The application initializes and registers a Quectel LTE module connected to the Raspberry Pi's serial interface.

2. **iperf Operation**:
   - After successfully registering the LTE module, the application initiates an iperf operation to test network performance.
   - It connects to a free iperf server (`209.58.159.68`) on ports `5201-5210` and conducts the test for `600 seconds`.
   - Results of the upload and download speeds are collected for performance evaluation.

3. **Displaying LTE Module Status**:
   - While the iperf operation is ongoing, the application continuously monitors the status of the LTE module.
   - It displays information on a ST7789 screen regarding the LTE module's registration status to the network or any other errors encountered.

## Purpose
The purpose of this application is to assess the network performance in the location where the LTE module is deployed. By conducting iperf tests and monitoring the LTE module's status, it provides insights into network connectivity and performance.

## Execution on Bootup
To run this application automatically on bootup, add the following command to your `ExecutionOnbootUp.sh` script:

```sudo /usr/bin/python /home/RPI_TestBenchForLTEModems/main.py >> /home/RPI_TestBenchForLTEModems/log.txt 2>&1```

This command ensures that the application (`main.py`) runs with root privileges and redirects both standard output and standard error to a log file for monitoring and debugging purposes.
Please ensure that the paths and filenames specified in the command are correct according to your system setup.

For any questions or issues regarding this application, please refer to the documentation or contact the developer.
