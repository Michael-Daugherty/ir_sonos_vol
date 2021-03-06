# Command Line Interface to Control Sonos Sound Systems
# sudo wget https://github.com/avantrec/soco-cli
# sudo pip install -U soco-cli
from soco_cli import api 

# https://luma-oled.readthedocs.io/en/latest/
# Enable i2c
#   sudo rasp-config > Interfaceing Options > i2c > yes
# Add User to i2c
#   sudo usermod -a -G i2c pi
#
# Display 128x64 (SSD1306) - wire color - SBC header (RPi 3 B+)
# Gnd (Pin.1) lft - bkl - Pin.01 (3V3)
# Vcc (Pin.2) mid - red - Pin.06 (Gnd)
# sCL (Pin.3) mid - grn - Pin.05 (gpIO.03)
# sDA (Pin.4) rht - blu - Pin.03 (gpIO.02)
# Determin display address: sudo -H pip3 install --upgrade luma.oled
from luma.core.interface.serial import i2c, spi, pcf8574
from luma.core.interface.parallel import bitbang_6800
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

from RPi import GPIO
import RPi.GPIO as GPIO
from time import time
import os

# ir reciever (TSOP38238) - wire color - SBC header (RPi 3 B+)
# Out (pin.1 lft) - blu wire - Pin.11 (gpIO.17)
# Gnd (pin.2 mid) - blk wire - Pin.09 (Gnd)
# V.s (pin.3 rht) - red wire - Pin.17 (3v3)
ir_pin=11

spkr="MySonos"
up=3772833823 # UP 0xe0e0e01f 0b11100000111000001110000000011111
dn=3772829743 # DN 0xe0e0d02f 0b11100000111000001101000000101111
mu=3772837903 # MU 0xe0e0f00f 0b11100000111000001111000000001111

def setup():
    GPIO.setmode(GPIO.BOARD)  # Numbers GPIOs by physical location
    GPIO.setup(ir_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def binary_aquire(pin, duration):
    # aquires data as quickly as possible
    t0 = time()
    results = []
    while (time() - t0) < duration:
        results.append(GPIO.input(pin))
    return results

def on_ir_receive(pinNo, bouncetime=300):
    # when edge detect is called (which requires less CPU than constant
    # data acquisition), we acquire data as quickly as possible
    data = binary_aquire(pinNo, bouncetime/1000.0)
    if len(data) < bouncetime:
        return
    rate = len(data) / (bouncetime / 1000.0)
    pulses = []
    i_break = 0
    # detect run lengths using the acquisition rate to turn the times in to microseconds
    for i in range(1, len(data)):
        if (data[i] != data[i-1]) or (i == len(data)-1):
            pulses.append((data[i-1], int((i-i_break)/rate*1e6)))
            i_break = i
    outbin = ""
    for val, us in pulses:
        if val != 1:
            continue
        if outbin and us > 2000:
            break
        elif us < 1000:
            outbin += "0"
        elif 1000 < us < 2000:
            outbin += "1"
    try:
        return int(outbin, 2)
    except ValueError:
        # probably an empty code
        return None

def destroy():
    GPIO.cleanup()

if __name__ == "__main__":
    setup()
    title = "IR_Sonos_Vol "
    spin = ["\\","|","/","-"]
    ln1 = title + spin[0]
    ln2 = ""
    with canvas(device) as draw:
        draw.text((0, 0), ln1, fill="white")
    try:
        MUTE="a"
        i=0
        print(title, "    ", spin[0], end="\r")
        while True:
            if i<3:
                i+=1
            else:
                i=0
            GPIO.wait_for_edge(ir_pin, GPIO.FALLING, timeout=500)
            code = on_ir_receive(ir_pin)
            if code==up:
                exit_code, output, error = api.run_command(spkr, "mute", "off")
                exit_code, output, error = api.run_command(spkr, "rel_vol", "+4")
                exit_code, output, error = api.run_command(spkr, "volume")
                print(title, output, "  ", spin[i], end="  \r")
                with canvas(device) as draw:
                    draw.text((30, 40), output, fill="white")

            elif code==dn:
                exit_code, output, error = api.run_command(spkr, "rel_vol", "-12")
                exit_code, output, error = api.run_command(spkr, "volume")
                print(title, output, "  ", spin[i], end="  \r")
            elif code==mu:
                # Ensure speaker is playing the AUX source
                exit_code, output, error = api.run_command(spkr, "line_in")
                if output=="off":
                    exit_code, output, error = api.run_command(spkr, "line_in", "on")
                
                exit_code, output, error = api.run_command(spkr, "mute")
                if output=="off":
                    exit_code, output, error = api.run_command(spkr, "mute", "on")
                    print(title, "Mute", spin[i], end="  \r")
                elif output=="on":
                    exit_code, output, error = api.run_command(spkr, "mute", "off")
                    exit_code, output, error = api.run_command(spkr, "volume")
                    print(title, output, "  ", spin[i], end="  \r")
            else:
                exit_code, output, error = api.run_command(spkr, "mute")
                if output=="on":
                    print(title, "Mute", spin[i], end="  \r")
                elif output=="off":    
                    exit_code, output, error = api.run_command(spkr, "volume")
                    print(title, output, "  ", spin[i], end="  \r")
    except KeyboardInterrupt:
        print("\r", title, " exited ", sep="")
destroy()
