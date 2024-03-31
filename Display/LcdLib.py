import time
import subprocess
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
from adafruit_rgb_display import st7789

# Alternatively load a TTF font.  Make sure the .ttf font file is in the
# same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)


# create connection dictionary
connectionStatus = {
    0: "No Connection",
    1: "Registered on Network",
    2: "Searching for Network",
    3: "Registration Denied",
    4: "Registration Unknown",
    5: "Registration Roaming",
    6: "Registered SMS Only",
    7: "Registered SMS and Data",
    8: "Emergency Calls Only",
    9: "Registered CSFB Only",
    10: "Registered CSFB SMS Only",
    11: "Registered CSFB SMS and Data",
}

def InitLcdScreen():
    """
    Initialize the LCD screen

    Returns:
        disp: the display object
    """

    # Configuration for CS and DC pins (these are FeatherWing defaults on M0/M4):
    cs_pin = digitalio.DigitalInOut(board.CE0)
    dc_pin = digitalio.DigitalInOut(board.D25)
    reset_pin = None

    # Config for display baudrate (default max is 24mhz):
    BAUDRATE = 64000000

    # Setup SPI bus using hardware SPI:
    spi = board.SPI()

    # Create the ST7789 display:
    disp = st7789.ST7789(
        spi,
        cs=cs_pin,
        dc=dc_pin,
        rst=reset_pin,
        baudrate=BAUDRATE,
        width=135,
        height=240,
        x_offset=53,
        y_offset=40,
    )

    # Create blank image for drawing.
    # Make sure to create image with mode 'RGB' for full color.
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
    image = Image.new("RGB", (width, height))
    rotation = 270

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=(0, 0, 0))
    disp.image(image, rotation)

    return disp

def DisplayText(disp, text, color="green"):
    """
    Display text on the LCD screen

    Args:
        disp: the display object
        text: the text to display

    Returns:
        None
    """

    # Create blank image for drawing.
    # Make sure to create image with mode 'RGB' for full color.
    height = disp.width  # we swap height/width to rotate it to landscape!
    width = disp.height
    image = Image.new("RGB", (width, height))
    rotation = 270

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=(0, 0, 0))

    if color == "red":
        # Draw the text
        draw.text((0, -2), text, font=font, fill="#FF0000")
    else:
        # Draw the text
        draw.text((0, -2), text, font=font, fill="#00FF00")

    # Display the image
    disp.image(image, rotation)

    return

def ShowTestUpdates(disp, network_status, runningTask, throughtput=""):
    """
    Show test updates on the LCD screen

    Args:
        disp: the display object
        network_status: the network status
        runningTask: the current running task
        throughtput: the throughput

    Returns:
        None
    """
    displayText = ""

    if network_status == "" or runningTask == "":
        return
    else:
        displayText += f"Network: {connectionStatus[network_status]}\n"
        displayText += f"Task: {runningTask}"

    if throughtput != "":
        displayText += f"\nThroughput: {throughtput}"

    DisplayText(disp, displayText)

    return

def DisplayError(disp, network_status, error):
    """
    Display error on the LCD screen

    Args:
        disp: the display object
        error: the error message

    Returns:
        None
    """
    
    DisplayText(disp, f"Network: {connectionStatus[network_status]}\nError!: \n{error}", "red")

    return

def DisplayTask(InstrumentData, displayQueue):
    """
    Display task on the LCD screen

    Args:
        InstrumentData: the instrument data
        displayQueue: the display queue to get the message

    Returns:
        None
    """
    # Initialize the LCD screen
    disp = InitLcdScreen()

    while InstrumentData["CloseAllThread"] != "yes":

        # Monitor the network status
        if 'Current_Reg_Stat' in InstrumentData:
            network_status = InstrumentData['Current_Reg_Stat']
        else:
            network_status = 0
        
        # Set network status to 0 if it is -1
        network_status = 0 if network_status == -1 else network_status

        # Check if the queue is not empty
        if not displayQueue.empty():
            event = displayQueue.get()
            if event:
                print(f"[Display] Received ERROR event: {event}")
                DisplayError(disp, network_status, event)
                break

        else:

            # Update status on the LCD screen
            if 'Final_Result' in InstrumentData:
                ShowTestUpdates(disp, network_status, InstrumentData["Running_Task"], InstrumentData["Final_Result"])
            else:
                ShowTestUpdates(disp, network_status, InstrumentData["Running_Task"])

        # wait for message to be displayed
        time.sleep(0.1)

    print("[Display] Closing the display thread")
    return