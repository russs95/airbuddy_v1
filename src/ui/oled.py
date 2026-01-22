import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from ui.headless import HeadlessDisplay



class OLED:
    """
    SSD1306 OLED helper with:
    - Google Fonts support (Arvo for title, Mulish for UI)
    - pixel-accurate centering
    - stable redraws (no undefined variables)
    """

    def __init__(self, width=128, height=64, addr=0x3C):
        # I2C init
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        self.width = width
        self.height = height

        # Persistent buffer
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # Fonts (safe fallback if missing)
        try:
            self.font_title = ImageFont.truetype(
                "assets/fonts/Arvo-Regular.ttf", 22
            )
            self.font_small = ImageFont.truetype(
                "assets/fonts/Mulish-Regular.ttf", 10
            )
            self.font_large = ImageFont.truetype(
                "assets/fonts/Mulish-Regular.ttf", 22
            )
        except Exception:
            self.font_title = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_large = ImageFont.load_default()
            # Dedicated spinner font (generic + reliable glyph coverage)
        try:
            self.font_spinner = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12
            )
        except Exception:
            self.font_spinner = self.font_large  # fallback

        self.oled.fill(0)
        self.oled.show()

        # Always define a generic fallback font handle
        self.font = self.font_small


    # ---------- Helpers ----------

    def clear(self):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()

    def _center_x(self, text, font):
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        return max(0, (self.width - text_w) // 2)

    def draw_centered(self, text, y, font):
        x = self._center_x(text, font)
        self.draw.text((x, y), text, font=font, fill=255)

    def text_size(self, text, font):
        # Pillow compatible text measurement
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]


    # ---------- screens ----------

    def show_waiting(self, line="Waiting for button"):
        """
        Idle screen — no spinner logic here.
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        self.draw_centered("airBuddy", 10, self.font_title)
        self.draw_centered(line, 34, self.font_small)

        self.oled.image(self.image)
        self.oled.show()

    def show_spinner_frame(self, frame):
        """
        Spinner-only frame, perfectly centered.

        `frame` can be:
          - string: drawn once (normal)
          - dict: {"text": str, "thick": bool} to draw with slight thickness pulse
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        thick = False
        if isinstance(frame, dict):
            text = frame.get("text", "")
            thick = bool(frame.get("thick", False))
        else:
            text = str(frame)

        # Measure text height precisely
        bbox = self.draw.textbbox((0, 0), text, font=self.font_spinner)
        text_h = bbox[3] - bbox[1]

        # Center vertically
        y = max(0, (self.height - text_h) // 2)

        # Draw centered
        self.draw_centered(text, y, self.font_spinner)

        # Optional thickness pulse: draw same text slightly lower
        if thick:
            self.draw_centered(text, y + 2, self.font_spinner)

        self.oled.image(self.image)
        self.oled.show()


    def show_results(self, temp_c, eco2_ppm, tvoc_ppb, rating="Ok", humidity=None, cached=False):
        """
        Show air readings. If cached=True, add a '(cached)' marker.
        humidity is optional.
        """
        self.clear()

        # Title line
        title = "Air data"
        if cached:
            title = "Air data (cached)"

        # You likely already have a title font; fall back safely
        title_font = self.font_title
        body_font = self.font_small


    # Draw title centered near top
        self.draw_centered(title, 0, title_font)

        # Body lines
        y = 26  # spacing below title (tune if needed)

        self.draw.text((2, y), f"Temp: {temp_c:>4.1f} C", font=body_font, fill=255)
        y += 12

        if humidity is not None:
            self.draw.text((2, y), f"Hum:  {humidity:>4.1f} %", font=body_font, fill=255)
            y += 12

        self.draw.text((2, y), f"eCO2: {eco2_ppm:>4d} ppm", font=body_font, fill=255)
        y += 12

        self.draw.text((2, y), f"TVOC: {tvoc_ppb:>4d} ppb", font=body_font, fill=255)
        y += 12

        self.draw.text((2, y), f"Air:  {rating}", font=body_font, fill=255)

        # Push to display
        self.oled.image(self.image)
        self.oled.show()


    def show_face(self, air_rating: str):
        """
        Full-screen face based on air_rating:
        'Very good', 'Good', 'Ok', 'Poor'
        """
        rating = (air_rating or "").strip().lower()

        # Clear
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # Face geometry
        cx, cy = self.width // 2, self.height // 2
        r = min(self.width, self.height) // 2 - 2

        # Face outline
        self.draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            outline=255,
            fill=0
        )

        # Eyes
        eye_r = 4
        eye_y = cy - 10
        eye_dx = 18
        self.draw.ellipse(
            (cx - eye_dx - eye_r, eye_y - eye_r,
             cx - eye_dx + eye_r, eye_y + eye_r),
            fill=255
        )
        self.draw.ellipse(
            (cx + eye_dx - eye_r, eye_y - eye_r,
             cx + eye_dx + eye_r, eye_y + eye_r),
            fill=255
        )

        # Mouth
        mouth_w = 46
        mouth_h = 26
        mouth_y = cy + 6
        box = (
            cx - mouth_w // 2,
            mouth_y - mouth_h // 2,
            cx + mouth_w // 2,
            mouth_y + mouth_h // 2,
        )

        if rating in ("very good", "verygood", "very_good"):
            self.draw.arc(box, start=200, end=340, fill=255, width=3)
        elif rating == "good":
            self.draw.arc(box, start=210, end=330, fill=255, width=3)
        elif rating == "ok":
            y = cy + 18
            self.draw.line((cx - 18, y, cx + 18, y), fill=255, width=3)
        else:  # Poor / default
            self.draw.arc(box, start=20, end=160, fill=255, width=3)

        self.oled.image(self.image)
        self.oled.show()

    @classmethod
    def try_create(cls):
        """
        Create a real OLED if present; otherwise return HeadlessDisplay.
        """
        try:
            return cls()
        except OSError as e:
            # Typical when OLED not attached: Remote I/O error / Input/output error
            print(f"[OLED] Not detected, running headless. ({e})", flush=True)
            return HeadlessDisplay()
        except Exception as e:
            print(f"[OLED] Failed to init OLED, running headless. ({e})", flush=True)
            return HeadlessDisplay()



