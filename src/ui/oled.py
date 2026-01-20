from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import busio


class OLED:
    def __init__(self, width=128, height=64, address=0x3C):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(
            width, height, self.i2c, addr=address
        )

        self.width = width
        self.height = height

        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

        self.clear()

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()

    def text(self, lines):
        self.clear()
        y = 0
        for line in lines:
            self.draw.text((0, y), line, font=self.font, fill=255)
            y += 16
        self.oled.image(self.image)
        self.oled.show()
