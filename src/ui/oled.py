import board
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
        i2c = board.I2C()
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

        # Use label font (Mulish 10)
        font = self.font_label

        bbox = self.draw.textbbox((0, 0), tag, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x = max(0, self.width - tw - 2)
        y = max(0, self.height - th - 6)

        self.draw.text((x, y), tag, font=font, fill=255)


    def _text_height(self, text: str, font):
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    # ---------- Screens -------------

    def show_waiting(self, line="Know your air."):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        self.draw_centered("airBuddy", 9, self.font_title)
        self.draw_centered(line, 38, self.font_small)

        self.oled.image(self.image)
        self.oled.show()

    def show_spinner_frame(self, frame):
        """
        Spinner-only frame, perfectly centered.

        frame can be:
          - string
          - dict:
              {"text": str, "thick": bool}              (legacy; bool => 3 lines)
              {"text": str, "thick_level": int}         (new; 0=1 line, 1=3 lines, 2=5 lines)
              {"text": str, "thickness_lines": int}     (optional; explicit 1/3/5)
        """
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # ----------------------------
        # Parse frame payload GPO
        # ----------------------------
        text = ""
        thickness_lines = 1  # default: 1-line

        if isinstance(frame, dict):
            text = str(frame.get("text", ""))

            # NEW: explicit thickness lines wins if provided
            if "thickness_lines" in frame:
                try:
                    thickness_lines = int(frame.get("thickness_lines", 1))
                except Exception:
                    thickness_lines = 1

            # NEW: thick_level => 0,1,2 => 1,3,5 lines
            elif "thick_level" in frame:
                try:
                    lvl = int(frame.get("thick_level", 0))
                except Exception:
                    lvl = 0
                thickness_lines = 1 if lvl <= 0 else (3 if lvl == 1 else 5)

            # LEGACY: thick bool => 3 lines
            else:
                thick = bool(frame.get("thick", False))
                thickness_lines = 3 if thick else 1

        else:
            text = str(frame)

        # Clamp to sane values
        if thickness_lines not in (1, 3, 5):
            thickness_lines = 1

        # ----------------------------
        # Center vertically and draw
        # ----------------------------
        text_h = self._text_height(text, self.font_spinner)
        y_center = (self.height - text_h) // 2

        if thickness_lines == 1:
            self.draw_centered(text, max(0, y_center), self.font_spinner)

        else:
            # Draw multiple copies vertically centered around y_center
            # 3 lines => offsets [-gap, 0, +gap]
            # 5 lines => offsets [-2gap, -gap, 0, +gap, +2gap]
            gap = 2  # px between duplicate draws (tweak if you want)

            half = thickness_lines // 2
            for k in range(-half, half + 1):
                y = y_center + (k * gap)
                y = max(0, min(self.height - text_h, y))
                self.draw_centered(text, y, self.font_spinner)

        self.oled.image(self.image)
        self.oled.show()

    def show_cached(self, reading, log_count: int):
        """
        Show last cached air reading in a compact two-column layout.
        Uses font_small everywhere.

        Layout (6s display controlled by main.py):
          Cached 14:35          Log: 234
          Temp: 32.2 °C     Air Index: 1
          CO2: 553            TVOC: 102
          Humidity: 79%
        """
        self.clear()
        font = self.font_small
        line_h = self._text_height("Ag", font) + 2

        x_left = 2
        x_right_margin = self.width - 2
        y = 4

        def draw_left(text):
            self.draw.text((x_left, y), text, font=font, fill=255)

        def draw_right(text):
            bbox = self.draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            self.draw.text((x_right_margin - w, y), text, font=font, fill=255)

        # --- Extract HH:MM from ISO timestamp safely ---
        time_part = "--:--"
        try:
            ts = str(getattr(reading, "timestamp_iso", "") or "")
            if "T" in ts:
                # 2026-01-23T14:35:12+07:00 -> "14:35"
                time_part = ts.split("T", 1)[1][:5]
            else:
                # fallback: if it's already "14:35" etc.
                time_part = ts[:5]
        except Exception:
            pass

        # --- Row 1 ---
        draw_left(f"Cached {time_part}")
        draw_right(f"Log: {log_count}")
        y += line_h

        # --- Row 2 ---
        draw_left(f"Temp: {reading.temp_c:.1f} °C")
        draw_right(f"Air Index: {reading.aqi}")
        y += line_h

        # --- Row 3 ---
        draw_left(f"CO2: {reading.eco2_ppm}")
        draw_right(f"TVOC: {reading.tvoc_ppb}")
        y += line_h

        # --- Row 4 ---
        draw_left(f"Humidity: {reading.humidity:.0f}%")

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
        self.draw_centered(heading, 5, self.font_medium)

        # Value centered
        value_h = self._text_height(value, self.font_title)
        y_value = max(0, (self.height - value_h) // 2 + 2)
        self.draw_centered(value, y_value, self.font_title)

        # Tag please
        self._draw_tag_bottom_right(tag)

        self.oled.image(self.image)
        self.oled.show()

    def show_face(self, air_rating: str):
        """
        Full-screen face based on air_rating + label underneath:
          "Air quality: Good"

        IMPORTANT:
          - The face outline (circle) and eyes are always the same.
          - ONLY the mouth changes based on the air category:
              * "Very good" -> big smile
              * "Good"      -> smile
              * "Ok"        -> flat / straight mouth
              * "Poor"      -> frown

        Note: no "cached/just now" tag on this screen.
        """

        # ----------------------------
        # Normalize rating text
        # ----------------------------
        rating_raw = (air_rating or "").strip() or "Ok"
        rating = rating_raw.strip().lower().replace("-", " ").replace("_", " ")
        rating = " ".join(rating.split())  # collapse whitespace

        # ----------------------------
        # Clear frame
        # ----------------------------
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        label = f"Air quality: {rating_raw}"

        # Reserve space for label at bottom
        label_h = self._text_height(label, self.font_small)
        label_y = self.height - label_h - 1  # 1px padding from bottom

        # ----------------------------
        # Face geometry (fits above label)
        # ----------------------------
        cx = self.width // 2
        top_pad = 2
        bottom_limit = label_y - 2  # gap above label
        available_h = max(0, bottom_limit - top_pad)

        # radius constrained by both height and width
        r = min((available_h // 2), (self.width // 2) - 2)
        r = max(10, r)

        cy = top_pad + r

        # ----------------------------
        # Draw face outline (circle)
        # ----------------------------
        self.draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, fill=0)

        # ----------------------------
        # Draw eyes (same for all ratings)
        # ----------------------------
        eye_r = max(2, r // 10)
        eye_y = cy - (r // 3)
        eye_dx = r // 2

        self.draw.ellipse(
            (cx - eye_dx - eye_r, eye_y - eye_r, cx - eye_dx + eye_r, eye_y + eye_r),
            fill=255
        )
        self.draw.ellipse(
            (cx + eye_dx - eye_r, eye_y - eye_r, cx + eye_dx + eye_r, eye_y + eye_r),
            fill=255
        )

        # ----------------------------
        # Mouth box (same position; shape depends on rating)
        # ----------------------------
        mouth_w = int(r * 1.2)
        mouth_h = int(r * 0.75)
        mouth_y = cy + (r // 4)

        box = (
            cx - mouth_w // 2, mouth_y - mouth_h // 2,
            cx + mouth_w // 2, mouth_y + mouth_h // 2
        )

        # ----------------------------
        # Mouth variants:
        #   Smiles use the LOWER arc of the box (around 20..160 degrees).
        #   Frowns use the UPPER arc of the box (around 200..340 degrees).
        # ----------------------------
        if rating in ("very good", "verygood"):
            # BIG SMILE
            self.draw.arc(box, start=20, end=160, fill=255, width=3)

        elif rating == "good":
            # SMILE (slightly flatter than very good)
            # Narrower arc range = flatter curve
            self.draw.arc(box, start=35, end=145, fill=255, width=3)

        elif rating == "ok":
            # FLAT / STRAIGHT mouth
            y = cy + (r // 2)
            self.draw.line((cx - (r // 2), y, cx + (r // 2), y), fill=255, width=3)

        else:
            # FROWN (Poor / default)
            self.draw.arc(box, start=200, end=340, fill=255, width=3)

        # ----------------------------
        # Label under face
        # ----------------------------
        self.draw_centered(label, label_y, self.font_small)

        # Push to display
        self.oled.image(self.image)
        self.oled.show()


    from typing import Optional  # <-- add near top of file

def show_settings(self, time_str: str, ip: Optional[str], power_tag: str):
    """
    Settings screen:
      - Time (large)
      - IP address or 'No connection'
      - Power tag bottom-right  kjlkjlkj
    """
    self.clear()

    self.draw_centered(time_str, 4, self.font_title)

    ip_text = ip if ip else "No connection"
    self.draw_centered(ip_text, 30, self.font_medium)

    self._draw_tag_bottom_right(power_tag)

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

