from machine import Pin
import utime
import urequests
from tm1638 import TM1638
import network
# Network
SSID = "WIFI"
PASSWORD = "PASSWORD"
# Ultrasonic Sensor
trigger = Pin(2, Pin.OUT)
echo = Pin(3, Pin.IN)
# LED and Buzzer setup
led = Pin(19, Pin.OUT)  # GPIO 19 for LED
buzzer = Pin(22, Pin.OUT)  # GPIO 22 for Buzzer
# TM1638 setup
stb = Pin(10, Pin.OUT)
clk = Pin(11, Pin.OUT)
dio = Pin(12, Pin.OUT)
tm = TM1638(stb=stb, clk=clk, dio=dio)

# Node-RED URL
url = "http://192.168.119.41:1880/data"
# Character map for TM1638
charmap = {
    '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
    '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
    ' ': 0x00, 'E': 0x79, 'R': 0x50, 'O': 0x5C, 'C': 0x39,
    'M': 0x37, '-': 0x40, '.': 0x80
}
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        timeout = 10
        while not wlan.isconnected() and timeout > 0:
            utime.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("Connected to Wi-Fi:", wlan.ifconfig())
    else:
        print("Failed to connect to Wi-Fi.")
connect_wifi()
def encode_with_dot(text):
    encoded = []
    max_segments = 8
    i = 0
    while i < len(text) and len(encoded) < max_segments:
        char = text[i]
        if i + 1 < len(text) and text[i + 1] == '.':
            encoded.append(charmap.get(char, 0x00) | 0x80)
            i += 1
        elif char != '.':
            encoded.append(charmap.get(char, 0x00))
        i += 1
    return [0x00] * (max_segments - len(encoded)) + encoded
def ultrasonnic():
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(5)
    trigger.low()
    timeout = 30000
    start_time = utime.ticks_us()
    signaloff = signalon = start_time
    while echo.value() == 0:
        signaloff = utime.ticks_us()
        if utime.ticks_diff(signaloff, start_time) > timeout:
            return float('inf')
    start_time = utime.ticks_us()
    while echo.value() == 1:
        signalon = utime.ticks_us()
        if utime.ticks_diff(signalon, start_time) > timeout:
            return float('inf')
    timepassed = signalon - signaloff
    return (timepassed * 0.0343) / 2
def alert(distance_cm):          
    if distance_cm > 50:  # ปลอดภัย
        led.off()
        buzzer.off()
    elif 30 < distance_cm <= 50:  # เตือนเบา
        led.on()
        buzzer.on()
        utime.sleep_ms(500)
        buzzer.off()
        led.off()
        utime.sleep_ms(500)
    elif 20 < distance_cm <= 30:  # เตือนกลาง
        led.on()
        buzzer.on()
        utime.sleep_ms(250)
        buzzer.off()
        led.off()
        utime.sleep_ms(250)
    elif 10 < distance_cm <= 20:  # เตือนถี่
        led.on()
        buzzer.on()
        utime.sleep_ms(100)
        buzzer.off()
        led.off()
        utime.sleep_ms(100)
    elif distance_cm <= 10:  # เตือนสูงสุด
        led.on()
        buzzer.on()  # เสียงต่อเนื่อง
        utime.sleep(0.1)
tm.clear()
print("TM1638 cleared and ready.")
while True:
    try:
        distance_cm = ultrasonnic()
    except Exception as e:
        distance_cm = float('inf')
        print(f"Error measuring distance: {e}")
    alert(distance_cm)  # เรียกใช้ระบบแจ้งเตือน
    display_text = " ERROR " if distance_cm == float('inf') else "{:.2f}".format(distance_cm) + "CE"
    display_text = display_text[-8:] if len(display_text) > 8 else " " * (8 - len(display_text)) + display_text
    encoded_data = encode_with_dot(display_text)
    # Update TM1638 display
    for i, value in enumerate(encoded_data):
        tm.write_data(i * 2, value)
    # Send data to Node-RED
    if distance_cm != float('inf'):
        try:
            headers = {"Content-Type": "text/plain"}
            response = urequests.post(url, data=str(distance_cm), headers=headers, timeout=0.01)
            print("Sent to Node-RED:", response.text)
            response.close()
        except Exception as e:
            print(f"Warning: {e}")
