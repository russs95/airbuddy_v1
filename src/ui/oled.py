import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class OLED:
    """
    SSD1306 OLED helper with:
    - TrueType fonts (bigger text)
    - pixel-centered text
    - optional partial redraw to reduce flicker
    """

    def __init__(self, width=128, height=64, addr=0x3C):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        self.width = width
        self.height = height

        # Single persistent buffer (avoid fill/show per frame)
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Fonts: use DejaVu (present on Raspberry Pi OS)
        # Small for labels, large for spinner
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        try:
            self.font_small = ImageFont.truetype(font_path, 12)
            self.font_large = ImageFont.truetype(font_path, 22)
        except Exception:
            # Fallback (tiny, but prevents crash)
            self.font_small = ImageFont.load_default()
            self.font_large = ImageFont.load_default()

        # Clear hardware once
        self.oled.fill(0)
        self.oled.show()

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()

    def _center_x(self, text, font):
        # textbbox returns (left, top, right, bottom)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        return max(0, (self.width - text_w) // 2)

    def draw_centered(self, text, y, font):
        x = self._center_x(text, font)
        self.draw.text((x, y), text, font=font, fill=255)

    def show_waiting(self, line="Waiting for button"):
        # Full screen draw (stable screen)
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.draw_centered("airBuddy v1", 6, self.font_small)
        self.draw_centered(line, 26, self.font_small)
        self.oled.image(self.image)
        self.oled.show()

    def show_spinner_frame(self, label, spinner_text):
        """
        Reduced flicker approach:
        - Draw label once at top (we still redraw, but we don't blank the entire screen)
        - Clear only the spinner region and redraw it.
        """
        # Draw label area (small clear)
        self.draw.rectangle((0, 0, self.width, 22), outline=0, fill=0)
        self.draw_centered(label, 4, self.font_small)

        # Clear spinner region only (middle/bottom)
        self.draw.rectangle((0, 22, self.width, self.height), outline=0, fill=0)
        # Center spinner vertically-ish; big font will occupy height ~22-26px
        self.draw_centered(spinner_text, 30, self.font_large)

        self.oled.image(self.image)
        self.oled.show()
