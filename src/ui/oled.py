import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

from ui.headless import HeadlessDisplay


class OLED:
    """
    SSD1306 OLED helper with:
    - 3 core typography styles + DejaVu spinner font
    - pixel-accurate centering
    - stable redraws
    """

    # ---- FONT PATHS ----
    ARVO_PATH = "assets/fonts/Arvo-Regular.ttf"
    MULISH_PATH = "assets/fonts/Mulish-Regular.ttf"
    SPINNER_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

    def __init__(self, width=128, height=64, addr=0x3C):
        # I2C init
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        self.width = width
        self.height = height

        # Persistent buffer
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # ---- FONTS ----
        # Three styles only: Title/Large, Medium, Small (+ spinner font)
        self.font_title = self._load_font(self.ARVO_PATH, 26, fallback=ImageFont.load_default())
        self.font_medium = self._load_font(self.MULISH_PATH, 14, fallback=self.font_title)
        self.font_small = self._load_font(self.MULISH_PATH, 10, fallback=ImageFont.load_default())

        self.font_spinner = self._load_font(self.SPINNER_PATH, 12, fallback=self.font_title)

        # Clear display
        self.oled.fill(0)
        self.oled.show()

    # ---------- Helpers ----------

    def _load_font(self, path: str, size: int, fallback):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return fallback

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

    def _draw_tag_bottom_right(self, tag: str):
        if not tag:
            return
        bbox = self.draw.textbbox((0, 0), tag, font=self.font_small)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = max(0, self.width - tw - 2)
        y = max(0, self.height - th - 1)
        self.draw.text((x, y), tag, font=self.font_small, fill=255)

    def _text_height(self, text: str, font):
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    # ---------- Screens ----------

    def show_waiting(self, line="Waiting for button"):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        self.draw_centered("airBuddy", 10, self.font_title)
        self.draw_centered(line, 34, self.font_small)

        self.oled.image(self.image)
        self.oled.show()

    def show_spinner_frame(self, frame):
        """
        Spinner-only frame, perfectly centered.

        frame can be:
          - string
          - dict: {"text": str, "thick": bool}
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        thick = False
        if isinstance(frame, dict):
            text = frame.get("text", "")
            thick = bool(frame.get("thick", False))
        else:
            text = str(frame)

        text_h = self._text_height(text, self.font_spinner)
        y = max(0, (self.height - text_h) // 2)

        self.draw_centered(text, y, self.font_spinner)

        if thick:
            self.draw_centered(text, y + 2, self.font_spinner)

        self.oled.image(self.image)
        self.oled.show()

    def show_metric(self, heading: str, value: str, tag: str = "just now"):
        """
        One metric per screen:
          - heading: Mulish 14
          - value: Arvo 22
          - tag: bottom-right ("just now" or "cached") in Mulish 10
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # Heading near top
        self.draw_centered(heading, 6, self.font_medium)

        # Value centered
        value_h = self._text_height(value, self.font_title)
        y_value = max(0, (self.height - value_h) // 2 - 2)
        self.draw_centered(value, y_value, self.font_title)

        # Tag
        self._draw_tag_bottom_right(tag)

        self.oled.image(self.image)
        self.oled.show()

    def show_face(self, air_rating: str, tag: str = "just now"):
        """
        Full-screen face based on air_rating + label underneath:
        "Air quality: Good"
        """
        rating_raw = (air_rating or "").strip()
        rating = rating_raw.lower()

        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        label = f"Air quality: {rating_raw if rating_raw else 'Ok'}"

        # Face geometry (leave space for label)
        cx = self.width // 2
        cy = (self.height // 2) - 6
        r = min(self.width, self.height) // 2 - 10

        # Outline
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, fill=0)

        # Eyes
        eye_r = 4
        eye_y = cy - 10
        eye_dx = 18
        self.draw.ellipse((cx - eye_dx - eye_r, eye_y - eye_r,
                           cx - eye_dx + eye_r, eye_y + eye_r), fill=255)
        self.draw.ellipse((cx + eye_dx - eye_r, eye_y - eye_r,
                           cx + eye_dx + eye_r, eye_y + eye_r), fill=255)

        # Mouth
        mouth_w = 46
        mouth_h = 26
        mouth_y = cy + 6
        box = (cx - mouth_w // 2, mouth_y - mouth_h // 2,
               cx + mouth_w // 2, mouth_y + mouth_h // 2)

        if rating in ("very good", "verygood", "very_good"):
            self.draw.arc(box, start=200, end=340, fill=255, width=3)
        elif rating == "good":
            self.draw.arc(box, start=210, end=330, fill=255, width=3)
        elif rating == "ok":
            y = cy + 18
            self.draw.line((cx - 18, y, cx + 18, y), fill=255, width=3)
        else:
            self.draw.arc(box, start=20, end=160, fill=255, width=3)

        # Label under face
        self.draw_centered(label, self.height - 14, self.font_small)

        # Tag
        self._draw_tag_bottom_right(tag)

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
            print(f"[OLED] Not detected, running headless. ({e})", flush=True)
            return HeadlessDisplay()
        except Exception as e:
            print(f"[OLED] Failed to init OLED, running headless. ({e})", flush=True)
            return HeadlessDisplay()
