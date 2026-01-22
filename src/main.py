import time

from ui.oled import OLED
from ui.spinner import Spinner
from ui.booter import Booter
from input.button import AirBuddyButton
from sensors.air import AirSensor


def main():
    oled = OLED()

    # Boot loader screen (title + progress bar)
    Booter(oled).show(duration=2.5, fps=12)

    spinner = Spinner(oled)
    btn = AirBuddyButton(gpio_pin=17)

    # Initialize air sensor manager
    air = AirSensor()

    # Start background logging:
    #   every 10 minutes, with 30s warmup
    air.start_periodic_logging(interval_seconds=600, warmup_seconds=30)

    while True:
        # ----------------------------
        # IDLE
        # ----------------------------
        oled.show_waiting("Waiting for button")
        btn.wait_for_press()
        time.sleep(0.08)  # debounce cushion

        # ----------------------------
        # SAMPLING (warmup during spinner)
        # ----------------------------
        cached = False

        try:
            air.begin_sampling(warmup_seconds=6, source="button")
            spinner.spin(duration=6)
            reading = air.finish_sampling(log=True)

            # If AirSensor returned a fallback record, mark cached
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


        # ----------------------------
        # MOOD FACE
        # ----------------------------
        oled.show_face(reading.rating)
        time.sleep(3)

        # ----------------------------
        # RESULTS SCREEN
        # ----------------------------
        oled.show_results(
            temp_c=reading.temp_c,
            humidity=reading.humidity,
            eco2_ppm=reading.eco2_ppm,
            tvoc_ppb=reading.tvoc_ppb,
            rating=reading.rating,
            cached=cached,
        )

        time.sleep(10)

        # ----------------------------
        # BACK TO IDLE
        # ----------------------------
        oled.clear()


if __name__ == "__main__":
    main()
