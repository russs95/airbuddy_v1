import time

from ui.oled import OLED
from ui.spinner import Spinner
from ui.booter import Booter
from input.button import AirBuddyButton
from sensors.air import AirSensor


def main():
    oled = OLED.try_create()

    # Boot loader only makes sense on a real display
    if oled.__class__.__name__ != "HeadlessDisplay":
        Booter(oled).show(duration=2.5, fps=12)
    else:
        print("[BOOT] airBuddy starting (headless)", flush=True)

    spinner = Spinner(oled)
    btn = AirBuddyButton(gpio_pin=17)

    # Initialize air sensor manager
    air = AirSensor()

    # Start background logging immediately (every 10 minutes, 30s warmup)
    air.start_periodic_logging(interval_seconds=600, warmup_seconds=30)

    while True:
        # ----------------------------
        # IDLE
        # ----------------------------
        oled.show_waiting("Know your air...")
        btn.wait_for_press()
        time.sleep(0.08)  # debounce cushion

        # ----------------------------
        # SAMPLING (button preempts background logging)
        # ----------------------------
        cached = False
        reading = None

        try:
            # Pause background logging to avoid sensor contention
            # (If not implemented yet, we'll add it in sensors/air.py)
            if hasattr(air, "pause_periodic_logging"):
                air.pause_periodic_logging()

            # Warmup occurs while spinner runs
            air.begin_sampling(warmup_seconds=6, source="button")
            spinner.spin(duration=6)
            reading = air.finish_sampling(log=True)

            # Mark cached only if AirSensor reports fallback
            if getattr(reading, "source", "") == "fallback":
                cached = True

        except Exception:
            last = air.get_last_logged()
            if last is None:
                oled.show_waiting("Sensor error")
                time.sleep(3)
                oled.clear()
                continue

            reading = last
            cached = True

        finally:
            # Resume background logging after button sampling
            if hasattr(air, "resume_periodic_logging"):
                air.resume_periodic_logging()

        # ----------------------------
        # DISPLAY SEQUENCE (2s each)
        # ----------------------------
        tag = "cached" if cached else "just now"

        oled.show_metric("Temperature", f"{reading.temp_c:.1f}°C", tag=tag)
        time.sleep(2)

        oled.show_metric("Humidity", f"{reading.humidity:.0f}%", tag=tag)
        time.sleep(2)

        oled.show_metric("CO₂ (ppm)", f"{reading.eco2_ppm}", tag=tag)
        time.sleep(2)

        oled.show_metric("TVOC (ppb)", f"{reading.tvoc_ppb}", tag=tag)
        time.sleep(2)

        # Face last (2s) — no tag
        oled.show_face(reading.rating)
        time.sleep(2)

        # Back to idle
        oled.clear()


if __name__ == "__main__":
    main()
