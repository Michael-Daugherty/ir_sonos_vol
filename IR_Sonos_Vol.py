from RPi import GPIO
import RPi.GPIO as GPIO
from time import time
import os
from soco_cli import api  # https://github.com/avantrec/soco-cli  # sudo pip install -U soco-cli

IR_PIN=12
SPKR="MySonos"
UP=3772833823 # UP 0xe0e0e01f 0b11100000111000001110000000011111
DN=3772829743 # DN 0xe0e0d02f 0b11100000111000001101000000101111
MU=3772837903 # MU 0xe0e0f00f 0b11100000111000001111000000001111

def setup():
    GPIO.setmode(GPIO.BOARD)  # Numbers GPIOs by physical location
    GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
    try:
        MUTE="a"
        i=0
        TITLE = " IR_Sonos_Vol"
        SPINNER = ["\\","|","/","-"]
        print(TITLE, "    ", SPINNER[0], end="\r")
        while True:
            if i<3:
                i+=1
            else:
                i=0
            GPIO.wait_for_edge(IR_PIN, GPIO.FALLING, timeout=500)
            code = on_ir_receive(IR_PIN)
            if code==UP:
                exit_code, output, error = api.run_command(SPKR, "mute", "off")
                exit_code, output, error = api.run_command(SPKR, "rel_vol", "+4")
                exit_code, output, error = api.run_command(SPKR, "volume")
                print(TITLE, output, "  ", SPINNER[i], end="  \r")
            elif code==DN:
                exit_code, output, error = api.run_command(SPKR, "rel_vol", "-12")
                exit_code, output, error = api.run_command(SPKR, "volume")
                print(TITLE, output, "  ", SPINNER[i], end="  \r")
            elif code==MU:
                # Ensure speaker is playing the AUX source
                exit_code, output, error = api.run_command(SPKR, "line_in")
                if output=="off":
                    exit_code, output, error = api.run_command(SPKR, "line_in", "on")
                
                exit_code, output, error = api.run_command(SPKR, "mute")
                if output=="off":
                    exit_code, output, error = api.run_command(SPKR, "mute", "on")
                    print(TITLE, "Mute", SPINNER[i], end="  \r")
                elif output=="on":
                    exit_code, output, error = api.run_command(SPKR, "mute", "off")
                    exit_code, output, error = api.run_command(SPKR, "volume")
                    print(TITLE, output, "  ", SPINNER[i], end="  \r")
            else:
                exit_code, output, error = api.run_command(SPKR, "mute")
                if output=="on":
                    print(TITLE, "Mute", SPINNER[i], end="  \r")
                elif output=="off":    
                    exit_code, output, error = api.run_command(SPKR, "volume")
                    print(TITLE, output, "  ", SPINNER[i], end="  \r")
    except KeyboardInterrupt:
        print("\r", TITLE, " exited ", sep="")
destroy()
