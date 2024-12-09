"""
2024. november 28.
Debreceni Egyetem - TTK Villamosmernok Tanszek - Embedded systems
-----------------------------------------------------------------
The following code uses of a Pico W microcontroller, a BME280, a hall sensor and lastly a MAX17043 fuel-gauge IC.
When executed it measures and uploads the collected data to a ThingSpeak server.

Made by: Zsolt Arany
"""

from machine import Pin, I2C, deepsleep
import bme280
import network
from time import sleep
import urequests
from max17043 import max17043

# Wi-Fi and ThingSpeak configuration
ssid= "---"
password= "---"
api_key= "---"
server= "---"
field_temp= 1
field_pres= 2
field_hum= 3
field_rain= 4
field_battery= 5

# Pin initialization
led=Pin("LED", Pin.OUT)
bme_3v3= Pin(2, Pin.OUT)
Q0= Pin(12, Pin.IN)
Q1= Pin(14, Pin.IN)
Q2= Pin(15, Pin.IN)
Q3= Pin(13, Pin.IN)
MR= Pin(11, Pin.OUT)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    if not wlan.isconnected():
        print("Waiting for connection...")
    while not wlan.isconnected():
        sleep(0.1)
    ip= wlan.ifconfig()[0]
    print(f"Connected on {ip}")

# Send data to Thingspeak
def send_TS(temp, pres, hum, rain, battery):
    url= f"{server}/update?api_key={api_key}&field{field_temp}={temp}&field{field_pres}={pres}&field{field_hum}={hum}&field{field_rain}={rain}&field{field_battery}={battery}"
    request= urequests.post(url)
    request.close()

# Collect data from BME280 sensor
def BME_read():
    bme_3v3.value(1)
    sleep(0.1)
    i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=40000)
    bme= bme280.BME280(i2c=i2c)
    sleep(5)
    t= float(bme.values[0])
    p= float(bme.values[1])
    h= float(bme.values[2])
    bme_3v3.value(0)
    return t, p, h

# Read and convert values from ripple counter and then reset it
def ripple_read():
    q0= Q0.value()
    q1= Q1.value()
    q2= Q2.value()
    q3= Q3.value()
    temp= (q0*2**0+q1*2**1+q2*2**2+q3*2**3)*2
    MR.value(1)
    sleep(0.5)
    MR.value(0)
    return temp

# Define functions to read and store the counter's value in a txt file
def cnt_read():
    with open("data.txt", "r") as file:
        content= file.read().strip()
        cnt_value, time= content.split(',')
        return int(cnt_value), int(time)
    
def cnt_write(cnt_value, time):
    with open("data.txt", "w") as file:
        file.write(f"{cnt_value},{time}")

while True:
    led.toggle()
    
    # Rain value from file and ripple counter and then store it in data.txt file
    cnt, time = cnt_read()
    cnt+= ripple_read()
    if (time==5):
        rain=cnt
        cnt=0
        time=0
    else:
        rain=0
        time+=1
    
    cnt_write(cnt, time)
    
    
    # Read values from BME280
    t, p, h= BME_read()

    # Read SoC of the lithium-ion battery
    m= max17043()
    battery= m.getSoc()
    
    print(t, p, h, rain, battery)
    
    # Connect to WiFi and send the data to ThingSpeak
    led.toggle()
    sleep(0.5)
    led.toggle()
    connect_wifi()
    led.toggle()
    sleep(0.5)
    led.toggle()
    send_TS(t, p, h, rain, battery)
     
    led.toggle()
    deepsleep(300000)