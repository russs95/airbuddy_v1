# src/sensors/air.py
from __future__ import annotations

import csv
import os
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple


@dataclass
class AirReading:
    timestamp_iso: str
    temp_c: float
    humidity: float
    eco2_ppm: int
    tvoc_ppb: int
    aqi: int
    rating: str
    source: str  # "button" | "scheduled" | "fallback"


class AirSensor:
    """
    ENS160 (AQI/eCO2/TVOC) + AHT21 (Temp/Humidity) sensor manager.

    Features:
      - Robust initialization + re-init on failure (beta friendly)
      - Warmup sampling (blocking or begin/finish non-blocking)
      - Logging to CSV
      - Scheduled background logging every 10 minutes (with 30s warmup)
      - Fallback to last logged reading if sensor read fails
    """

    def __init__(
            self,
            log_dir: str = "logs",
            log_filename: str = "air_records.csv",
            i2c_bus: int = 1,
    ):
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, log_filename)
        self.i2c_bus = i2c_bus

        self._lock = threading.Lock()

        # Underlying device handles
        self._i2c = None
        self._ens = None
        self._aht = None

        # Warmup state for non-blocking sampling
        self._warmup_until: Optional[float] = None
        self._warmup_source: Optional[str] = None

        # Scheduler thread control
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Ensure logs path exists
        os.makedirs(self.log_dir, exist_ok=True)
        self._ensure_log_header()

        # Try to init once (non-fatal if it fails)
        self._try_init()

    # ----------------------------
    # INITIALIZATION / RE-INIT
    # ----------------------------
    def _try_init(self) -> bool:
        """
        Attempt to initialize I2C + sensors. Returns True on success, False on failure.
        Never raises (beta-friendly).
        """
        try:
            import board
            import busio
            import adafruit_ens160
            import adafruit_ahtx0

            # Create bus fresh each time we init (helps after transient errors)
            self._i2c = busio.I2C(board.SCL, board.SDA)

            # IMPORTANT: If bus is busy, busio may block; keep it simple.
            self._ens = adafruit_ens160.ENS160(self._i2c)
            self._aht = adafruit_ahtx0.AHTx0(self._i2c)

            return True
        except Exception:
            # Mark as unavailable
            self._i2c = None
            self._ens = None
            self._aht = None
            return False

    def _available(self) -> bool:
        return (self._ens is not None) and (self._aht is not None)

    # ----------------------------
    # RATING / MAPPING
    # ----------------------------
    @staticmethod
    def _rating_from_aqi(aqi: int) -> str:
        """
        Map ENS160 AQI (1..5) to your four-level rating strings.
        """
        # ENS160 AQI commonly:
        # 1=Excellent, 2=Good, 3=Moderate, 4=Poor, 5=Unhealthy
        if aqi <= 1:
            return "Very good"
        if aqi == 2:
            return "Good"
        if aqi == 3:
            return "Ok"
        return "Poor"

    # ----------------------------
    # LOGGING
    # ----------------------------
    def _ensure_log_header(self) -> None:
        """
        Create CSV header if file doesn't exist or is empty.
        """
        needs_header = (not os.path.exists(self.log_path)) or (os.path.getsize(self.log_path) == 0)
        if needs_header:
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["timestamp_iso", "temp_c", "humidity", "eco2_ppm", "tvoc_ppb", "aqi", "rating", "source"])

    def _append_log(self, r: AirReading) -> None:
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([r.timestamp_iso, f"{r.temp_c:.2f}", f"{r.humidity:.2f}", r.eco2_ppm, r.tvoc_ppb, r.aqi, r.rating, r.source])

    def get_last_logged(self) -> Optional[AirReading]:
        """
        Return the last logged reading from CSV (or None if no data).
        """
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            return None

        try:
            with open(self.log_path, "r", newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
                # rows[0] is header; last data row is at end
                for row in reversed(rows[1:]):
                    if not row or len(row) < 8:
                        continue
                    ts, temp_c, hum, eco2, tvoc, aqi, rating, source = row[:8]
                    return AirReading(
                        timestamp_iso=ts,
                        temp_c=float(temp_c),
                        humidity=float(hum),
                        eco2_ppm=int(float(eco2)),
                        tvoc_ppb=int(float(tvoc)),
                        aqi=int(float(aqi)),
                        rating=str(rating),
                        source=str(source),
                    )
        except Exception:
            return None

    # ----------------------------
    # TIME / TIMESTAMP
    # ----------------------------
    @staticmethod
    def _now_iso_local() -> str:
        # Store in ISO with local offset for human-readability on the Pi
        return datetime.now().astimezone().isoformat(timespec="seconds")

    # ----------------------------
    # SENSOR READ CORE
    # ----------------------------
    def _read_once(self, source: str) -> AirReading:
        """
        Read one set of values from sensors.
        Raises on failure.
        """
        if not self._available():
            raise RuntimeError("Sensor not initialized")

        # Read temperature/humidity first
        temp_c = float(self._aht.temperature)
        humidity = float(self._aht.relative_humidity)

        # Apply compensation to ENS160 if the library supports it
        # (Different library versions expose different APIs)
        try:
            if hasattr(self._ens, "temperature_compensation"):
                self._ens.temperature_compensation = temp_c
            if hasattr(self._ens, "humidity_compensation"):
                self._ens.humidity_compensation = humidity
            if hasattr(self._ens, "set_environment"):
                self._ens.set_environment(temp_c, humidity)
        except Exception:
            # Compensation is nice-to-have; don't fail reads if it errors
            pass

        # Read ENS160 outputs
        eco2_ppm = int(self._ens.eCO2)
        tvoc_ppb = int(self._ens.TVOC)
        aqi = int(self._ens.AQI)
        rating = self._rating_from_aqi(aqi)

        return AirReading(
            timestamp_iso=self._now_iso_local(),
            temp_c=temp_c,
            humidity=humidity,
            eco2_ppm=eco2_ppm,
            tvoc_ppb=tvoc_ppb,
            aqi=aqi,
            rating=rating,
            source=source,
        )

    # ----------------------------
    # BLOCKING SAMPLE (EASY)
    # ----------------------------
    def sample_blocking(self, warmup_seconds: float, source: str, log: bool = True) -> AirReading:
        """
        Warm up, read, log. If sensor fails, return last logged value (fallback).
        """
        with self._lock:
            # Try init if needed
            if not self._available():
                self._try_init()

            # Warmup (blocking)
            if warmup_seconds > 0:
                time.sleep(warmup_seconds)

            try:
                r = self._read_once(source=source)
                if log:
                    self._append_log(r)
                return r
            except Exception:
                # Try re-init once then retry read quickly
                self._try_init()
                try:
                    r = self._read_once(source=source)
                    if log:
                        self._append_log(r)
                    return r
                except Exception:
                    # Fallback to last logged value (if any)
                    last = self.get_last_logged()
                    if last is None:
                        # If nothing logged yet, raise a clear error
                        raise RuntimeError("Sensor read failed and no fallback record exists")
                    # Mark fallback source + timestamp now (so UI can show current time)
                    return AirReading(
                        timestamp_iso=self._now_iso_local(),
                        temp_c=last.temp_c,
                        humidity=last.humidity,
                        eco2_ppm=last.eco2_ppm,
                        tvoc_ppb=last.tvoc_ppb,
                        aqi=last.aqi,
                        rating=last.rating,
                        source="fallback",
                    )

    # ----------------------------
    # NON-BLOCKING WARMUP (FOR SPINNER IN MAIN)
    # ----------------------------
    def begin_sampling(self, warmup_seconds: float, source: str) -> None:
        """
        Start a warmup window. You can run the spinner while time passes,
        then call finish_sampling() to read + log.
        """
        with self._lock:
            if not self._available():
                self._try_init()
            self._warmup_until = time.time() + max(0.0, float(warmup_seconds))
            self._warmup_source = source

    def is_ready(self) -> bool:
        with self._lock:
            if self._warmup_until is None:
                return True
            return time.time() >= self._warmup_until

    def finish_sampling(self, log: bool = True) -> AirReading:
        """
        Complete a non-blocking sampling cycle: read + log (or fallback).
        """
        with self._lock:
            source = self._warmup_source or "button"
            # If warmup wasn't finished yet, do not block here; caller controls timing
            if self._warmup_until is not None and time.time() < self._warmup_until:
                raise RuntimeError("Warmup not complete yet")

            # Reset warmup state
            self._warmup_until = None
            self._warmup_source = None

        # Use blocking sample with warmup_seconds=0 (we already waited externally)
        return self.sample_blocking(warmup_seconds=0, source=source, log=log)

    # ----------------------------
    # SCHEDULED LOGGING (EVERY 10 MIN, 30s WARMUP)
    # ----------------------------
    def start_periodic_logging(self, interval_seconds: int = 600, warmup_seconds: int = 30) -> None:
        """
        Start a background thread that logs air readings every `interval_seconds`
        with `warmup_seconds` warmup per scheduled read.
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return  # already running

        self._stop_event.clear()

        def _runner():
            # Align to interval boundaries (optional but nice)
            next_time = time.time()
            while not self._stop_event.is_set():
                now = time.time()
                if now >= next_time:
                    # Do scheduled sample + log; fall back if needed
                    try:
                        self.sample_blocking(warmup_seconds=warmup_seconds, source="scheduled", log=True)
                    except Exception:
                        # If absolutely nothing exists to fall back to, ignore and keep going
                        pass
                    next_time = now + interval_seconds
                time.sleep(0.5)

        self._scheduler_thread = threading.Thread(target=_runner, name="airbuddy-scheduler", daemon=True)
        self._scheduler_thread.start()

    def stop_periodic_logging(self) -> None:
        self._stop_event.set()
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=2.0)
