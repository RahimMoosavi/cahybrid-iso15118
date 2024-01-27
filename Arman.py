import Adafruit_MCP4725
import Adafruit_ADS1x15
import time
import board
from digitalio import DigitalInOut, Direction

# Note you can change the I2C address from its default (0x62), and/or the I2C
# bus by passing in these optional parameters:
#dac = Adafruit_MCP4725.MCP4725(address=0x49, busnum=1)
class Arman:
    GAIN=1
    def __init__(self):
        self.dac = Adafruit_MCP4725.MCP4725(address=0x61, busnum=1)
        self.adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)
            # setup Pi pins as output for LEDs
        self.green_led = DigitalInOut(board.D17)
        self.green_led.direction = Direction.OUTPUT
        self.green_led.value = True

    def set_dac(self, voltage):
        self.dac.set_voltage(voltage)
    
    def set_adc(self, voltage):
        self.adc.set_voltage(voltage)
        
    def get_adc(self, channel):
        return self.adc.read_adc(channel, gain=1)
    
    def get_adc(self, channel):
        return self.adc.read_adc(channel, gain=1)
    
   
# Loop forever alternating through different voltage outputs.
print('Press Ctrl-C to quit...')
while True:
    for i in range(0, 4096):
        time.sleep(0.001)
        print(f'ADC ch2 voltage is {adc.read_adc(2, gain=GAIN)}')
        time.sleep(0.001)
        dac.set_voltage(i)
        print(f'DAC voltage is {i}!')
        if(int(i/100)%2 == 0):
            green_led.value = False
        else:
            green_led.value = True
        ##time.sleep(0.1)
            

            