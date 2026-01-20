import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class OLED:
    """
    SSD1306 OLED helper with:
    - Google Fonts support (Arvo for title, Mulish for UI)
    - pixel-accurate centering
    - optional partial redraw to reduce flicker
    """

    def __init__(self, width=128, height=64, addr=0x3C):
        # I2C init
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        self.width = width
        self.height = height

        # Persistent buffer (avoid excessive full clears)
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Load custom fonts (Arvo + Mulish) from repo assets
        try:
            self.font_title = ImageFont.truetype("assets/fonts/Arvo-Regular.ttf", 24)
            self.font_small = ImageFont.truetype("assets/fonts/Mulish-Regular.ttf", 13)
            self.font_large = ImageFont.truetype("assets/fonts/Mulish-Regular.ttf", 18)
        except Exception as e:
            # Fallback fonts to avoid crashing if fonts aren't present yet
            print("Font load failed, using defaults:", e)
            self.font_title = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_large = ImageFont.load_default()

        # Clear hardware once
        self.oled.fill(0)
        self.oled.show()

    def clear(self):
        """Clear entire display."""
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()

    def _center_x(self, text, font):
        """Compute x position to center `text` for a given font."""
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        return max(0, (self.width - text_w) // 2)

    def draw_centered(self, text, y, font):
        """Draw text centered horizontally at y."""
        x = self._center_x(text, font)
        self.draw.text((x, y), text, font=font, fill=255)

    def show_waiting(self, line="Waiting for button"):
        """
        Idle screen (no variables; stable, minimal flicker).
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        self.draw_centered("airBuddy", 10, self.font_title)
        self.draw_centered(line, 34, self.font_small)

        self.oled.image(self.image)
        self.oled.show()

    def show_spinner_frame(self, label, spinner_text):
        """
        Reduced flicker approach:
        - Clear and redraw only the label band and spinner region.
        """
        # Label area
        self.draw.rectangle((0, 0, self.width, 22), outline=0, fill=0)
        self.draw_centered(label, 3, self.font_small)

        # Spinner area
        self.draw.rectangle((0, 22, self.width, self.height), outline=0, fill=0)
        self.draw_centered(spinner_text, 30, self.font_large)

        self.oled.image(self.image)
        self.oled.show()

    def show_results(self, temp_c, eco2_ppm, tvoc_ppb, rating="GOOD"):
        """
        Stable, non-animated results screen (minimal flicker).
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # Values (left aligned for fast scanning)
        y = 22
        self.draw.text((2, y), f"Temp: {temp_c:>4.1f} C", font=self.font_small, fill=255)
        self.draw.text((2, y + 14), f"eCO2: {eco2_ppm:>4d} ppm", font=self.font_small, fill=255)
        self.draw.text((2, y + 28), f"TVOC: {tvoc_ppb:>4d} ppb", font=self.font_small, fill=255)

        # Rating (centered near bottom)
        self.draw_centered(f"AIR: {rating}", 50, self.font_small)

        self.oled.image(self.image)
        self.oled.show()
