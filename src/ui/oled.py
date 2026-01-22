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
    # --------------------------------------------------
    # I2C / DISPLAY INITIALIZATION
    # --------------------------------------------------
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=addr)

        self.width = width
        self.height = height

        # Persistent drawing buffer (prevents flicker)
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

        # --------------------------------------------------
        # FONT DEFINITIONS
        # --------------------------------------------------
        # Typography system:
        # - title   : headings / hero text
        # - medium  : primary UI text (with vertical breathing room)
        # - small   : secondary UI text
        # - label   : compact labels / metadata
        # - spinner : fixed-width animation glyphs

        self.font_title = self._load_font(
            self.ARVO_PATH, 26, fallback=ImageFont.load_default()
        )

        self.font_medium = self._load_font(
            self.MULISH_PATH, 16, fallback=self.font_title
        )

        self.font_small = self._load_font(
            self.MULISH_PATH, 12, fallback=ImageFont.load_default()
        )

        # NEW: Label font (compact, quiet UI text)
        self.font_label = self._load_font(
            self.MULISH_PATH, 10, fallback=self.font_small
        )

        # Spinner / monospace animation font
        self.font_spinner = self._load_font(
            self.SPINNER_PATH, 10, fallback=self.font_title
        )

        # --------------------------------------------------
        # FONT-SPECIFIC LAYOUT TWEAKS
        # --------------------------------------------------
        # Extra vertical breathing room for medium text
        # (applied manually when drawing text)
        self.font_medium_padding = 2  # px above + below

        # --------------------------------------------------
        # CLEAR DISPLAY ON INIT
        # --------------------------------------------------
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
        y = max(0, self.height - th - 6)
        self.draw.text((x, y), tag, font=self.font_small, fill=255)

    def _text_height(self, text: str, font):
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    # ---------- Screens ----------

    def show_waiting(self, line="Know your air."):
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

    def show_face(self, air_rating: str):
        """
        Full-screen face based on air_rating + label underneath:
        "Air quality: Good"

        Note: no "cached/just now" tag on this screen.
        """
        rating_raw = (air_rating or "").strip() or "Ok"
        rating = rating_raw.lower()

        # Clear
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        label = f"Air quality: {rating_raw}"

        # --- Reserve space for label at bottom ---
        label_h = self._text_height(label, self.font_small)
        label_y = self.height - label_h - 1  # 1px padding from bottom

        # --- Face geometry (guaranteed to fit above label) ---
        cx = self.width // 2

        # Top padding for circle and bottom limit right above label
        top_pad = 2
        bottom_limit = label_y - 2  # 2px gap above label

        # Available vertical span for the circle region
        available_h = max(0, bottom_limit - top_pad)

        # Choose radius based on available height and width
        r = min((available_h // 2), (self.width // 2) - 2)
        r = max(10, r)  # keep it sane even if fonts change

        cy = top_pad + r  # circle touches top_pad nicely

        # Outline
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, fill=0)

        # Eyes (scaled to radius so they stay inside the circle)
        eye_r = max(2, r // 10)
        eye_y = cy - (r // 3)
        eye_dx = r // 2

        self.draw.ellipse((cx - eye_dx - eye_r, eye_y - eye_r,
                           cx - eye_dx + eye_r, eye_y + eye_r), fill=255)
        self.draw.ellipse((cx + eye_dx - eye_r, eye_y - eye_r,
                           cx + eye_dx + eye_r, eye_y + eye_r), fill=255)

        # Mouth (scaled)
        mouth_w = int(r * 1.2)
        mouth_h = int(r * 0.75)
        mouth_y = cy + (r // 4)

        box = (cx - mouth_w // 2, mouth_y - mouth_h // 2,
               cx + mouth_w // 2, mouth_y + mouth_h // 2)

        if rating in ("very good", "verygood", "very_good"):
            self.draw.arc(box, start=200, end=340, fill=255, width=3)
        elif rating == "good":
            self.draw.arc(box, start=210, end=330, fill=255, width=3)
        elif rating == "ok":
            y = cy + (r // 2)
            self.draw.line((cx - (r // 2), y, cx + (r // 2), y), fill=255, width=3)
        else:
            self.draw.arc(box, start=20, end=160, fill=255, width=3)

        # Label under face
        self.draw_centered(label, label_y, self.font_small)

        # Push to display
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
