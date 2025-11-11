# Copyright 2025 IO Club
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""spnoiser package main module.

This module exposes `main(argv=None)` so it can be installed as a console script.
"""

import argparse
import curses
import math
import sys
import threading
import time

import sounddevice as sd
import soundfile as sf

if __name__ == "__main__":
    import os.path

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from spnoiser.ui.components import Monitor
from spnoiser.ui.core import max_area_of

DEFAULT_NOISE = "beep"
DEFAULT_MAX_SECONDS = 60


class App:
    """Main application class for spnoiser."""

    _stdscr: curses.window
    _noise_text: str
    _max_time: int
    _sound_file_path: str | None
    _volume: float

    _start_time: float
    _beep_enabled: bool
    _last_beep: float

    def __init__(
        self,
        stdscr: curses.window,
        noise_text: str,
        max_time: int,
        sound_file_path: str | None,
        volume: float,
    ) -> None:
        self._stdscr = stdscr
        self._noise_text = noise_text
        self._max_time = max_time
        self._sound_file_path = sound_file_path
        self._volume = volume

        self._beep_enabled = sound_file_path is None

        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.timeout(200)
        try:
            stdscr.keypad(True)
            mask = curses.ALL_MOUSE_EVENTS
            report = getattr(curses, "REPORT_MOUSE_POSITION", 0)
            curses.mousemask(mask | report)
            curses.mouseinterval(0)
        except Exception as err:
            print(f"Error setting up curses: {type(err).__name__}: {err}")

    @property
    def noise_text(self) -> str:
        return self._noise_text

    @property
    def max_time(self) -> int:
        return self._max_time

    @property
    def sound_file_path(self) -> str | None:
        return self._sound_file_path

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def beep_enabled(self) -> bool:
        return self._beep_enabled

    def mainloop(self) -> None:
        """Main application loop."""

        stdscr = self._stdscr
        self._start_time = start_time = time.monotonic()
        self._last_beep = start_time

        if not self._beep_enabled:
            self._play_sound_noblock()

        try:
            while self._frame():
                time.sleep(App.FRAME_INTERVAL)
        finally:
            if not self._beep_enabled:
                sd.stop()

        try:
            stdscr.nodelay(False)
            stdscr.erase()
        except Exception:
            pass

    def _play_sound_noblock(self) -> None:
        """Play sound in a non-blocking thread."""

        def play_sound_block() -> None:
            try:
                while True:
                    data, samplerate = sf.read(self.sound_file_path, dtype="float32")
                    data *= self._volume
                    sd.play(data, samplerate=samplerate)
                    sd.wait()
            except Exception as err:
                sd.stop()
                print(f"Error starting sound playback:\n{type(err).__name__}: {err}")
                self._beep_enabled = True

        threading.Thread(
            target=play_sound_block,
            daemon=True,
        ).start()

    def _frame(self) -> bool:
        """Single frame of the main loop."""
        stdscr = self._stdscr
        ch = stdscr.getch()
        if ch != -1:
            if ch == 27:
                # ESC key pressed
                return False
            # consume mouse events so terminal does not scroll (wheel)
            if ch == getattr(curses, "KEY_MOUSE", -1):
                try:
                    _ = curses.getmouse()
                except Exception:
                    pass
                return True

        remaining_seconds = self.remaining_seconds()
        if remaining_seconds is not None and remaining_seconds <= 0:
            return False

        stdscr.erase()
        try:
            Monitor(
                stdscr=stdscr,
                area=max_area_of(stdscr),
                noise_text=self._noise_text,
                remaining_seconds=remaining_seconds,
            ).draw()
        except Exception as err:
            # keep loop alive even if drawing fails
            print(f"Rendering error:\n{type(err).__name__}: {err}")

        stdscr.refresh()

        if self.beep_enabled:
            now = time.monotonic()
            if now - self._last_beep >= App.BEEP_INTERVAL:
                try:
                    curses.beep()
                except Exception:
                    pass
                self._last_beep = now

        return True

    def remaining_seconds(self) -> int | None:
        if self._max_time == 0:
            return None
        return max(0, int(self._max_time - (time.monotonic() - self._start_time)))

    FRAME_INTERVAL = 0.8
    BEEP_INTERVAL = 1.0

    @classmethod
    def create_and_run(
        cls,
        stdscr: curses.window,
        noise_text: str,
        max_time: int,
        sound_file_path: str | None,
        volume: float,
    ) -> None:
        """Create and run the application."""
        app = cls(stdscr, noise_text, max_time, sound_file_path, volume)
        app.mainloop()


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="SPNoiser: Run to annoy the user")
    parser.add_argument(
        "-n",
        "--noise",
        default=DEFAULT_NOISE,
        help=f"Annoying text (default: '{DEFAULT_NOISE}')",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=DEFAULT_MAX_SECONDS,
        help=f"Max annoying time in seconds (default: {DEFAULT_MAX_SECONDS})",
    )
    parser.add_argument(
        "-s",
        "--sound",
        type=str,
        default=None,
        help="Path to the audio file to loop (WAV recommended). If not specified, the system beep sound will be used.",
    )
    parser.add_argument(
        "-v",
        "--volume",
        type=float,
        default=1.0,
        help="Volume for the audio file playback (default: 1.0)",
    )
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        print(f"Error in arguments: {err}")
        return 2

    try:
        curses.wrapper(
            App.create_and_run, args.noise, args.time, args.sound, args.volume
        )
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as err:
        print(f"Error:\n{type(err).__name__}: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
