"""
airBuddy v1
Main entry point.

For now:
- Initialize OLED
- Run a spinner test to confirm UI loop works

Later this will:
- Wait for button press
- Spin while reading sensors
- Display air quality results
"""

import time

from ui.oled import OLED
from ui.spinner import Spinner


def main():
    # Initialize OLED
    oled = OLED()
    oled.text([
        "airBuddy v1",
        "Booting..."
    ])
    time.sleep(1.5)

    # Initialize spinner (spinner writes directly to OLED)
    spinner = Spinner(oled)

    # Spinner test
    spinner.spin(duration=3, label="Testing spinner")

    # Final confirmation screen
    oled.text([
        "OLED OK",
        "Spinner OK",
        "",
        "Ready."
    ])
    time.sleep(3)

    # Clear display before exit (optional)
    oled.clear()


if __name__ == "__main__":
    main()
