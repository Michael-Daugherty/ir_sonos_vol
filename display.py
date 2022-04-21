import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess

RST = 0

disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
font = ImageFont.load_default()
disp.begin()
disp.clear()
disp.display()
width = disp.width
height = disp.height
padding = -2
top = padding
bottom = height-padding

image1 = Image.new('1', (width, height))
draw = ImageDraw.Draw(image1)
draw.rectangle((0,0,width,height), outline=0, fill=0)
disp.clear()
disp.display()

def updisp(sym, cod, vol, mut):
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((0, top+00), sym+"   IR SONOS VOL   "+sym,     font=font, fill=255)
    draw.text((0, top+25), "IR "+cod,     font=font, fill=255)
    draw.text((0, top+50), "VOLUME "+vol+mut, font=font, fill=255)
    disp.image(image1)
    disp.display()

t=time.perf_counter()
i=0
spin = "|/-\\"
while i < len(spin):


    if time.perf_counter() - t < 8:
        updisp(spin[i], "123456789", " 26", " - Muted")
        time.sleep(0.2)
        if i==3:
            i = 0
        else:
            i += 1
    else:
        disp.clear()
        disp.display()
