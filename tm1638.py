from machine import Pin
import time
class TM1638:
    def __init__(self, stb, clk, dio):
        self.stb = stb
        self.clk = clk
        self.dio = dio
        self.stb.init(Pin.OUT, value=1)
        self.clk.init(Pin.OUT, value=1)
        self.dio.init(Pin.OUT, value=1)
        self.send_command(0x40)
        self.brightness(7)
        self.clear()
    def send_command(self, cmd):
        self.stb.low()
        self.shift_out(cmd)
        self.stb.high()
    def shift_out(self, data):
        for i in range(8):
            self.clk.low()
            self.dio.value((data >> i) & 1)
            self.clk.high()
    def write_data(self, address, data):
        self.send_command(0x44)  # Fixed address mode
        self.stb.low()
        self.shift_out(0xC0 | address)
        self.shift_out(data)
        self.stb.high()
    def clear(self):
        for i in range(16):
            self.write_data(i, 0x00)
    def brightness(self, level):
        if level < 0: level = 0
        if level > 7: level = 7
        self.send_command(0x88 | level)
    def show_text(self, text):
        encoded = self.encode_text(text)
        for i in range(8):
            self.write_data(i * 2, encoded[i] if i < len(encoded) else 0)

    def encode_text(self, text):
        charmap = {
            '0': 0x3F, '1': 0x06, '2': 0x5B, '3': 0x4F, '4': 0x66,
            '5': 0x6D, '6': 0x7D, '7': 0x07, '8': 0x7F, '9': 0x6F,
            'A': 0x77, 'B': 0x7C, 'C': 0x39, 'D': 0x5E, 'E': 0x79, 'F': 0x71,
            '-': 0x40, '_': 0x08, ' ': 0x00
        }
        encoded = []
        for char in text.upper():
            encoded.append(charmap.get(char, 0x00))
        return encoded
    def test(self):
        self.show_text("HELLO123")
        time.sleep(2)
        self.clear()

