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

"""UI components for spnoiser implemented as classes.

Each component takes its parameters in __init__ and exposes a parameterless draw()
method that renders itself into the provided curses stdscr.
"""

from abc import abstractmethod
from typing import Callable

from spnoiser.utils import require
from spnoiser.importypes import curses
from spnoiser.ui.core import Rect, ScreenElement, Vector2D

type Content = Callable[[Rect], None]


class BorderBox(ScreenElement):
    """Box that draws a border around the entire terminal window."""

    __content: Content

    def __init__(self, stdscr: curses.window, area: Rect, content: Content) -> None:
        super().__init__(stdscr, area)
        self.__content = content

    def draw(self) -> None:
        """Draw the border box."""
        try:
            height, width = self._size
            horizon_border = (
                "+" + ("-" * max(0, width - 2)) + "+" if width >= 2 else "+"
            )
            vector_border = "|"

            self._draw_str(0, 0, horizon_border)

            for y in range(1, height - 1):
                self._draw_str(y, 0, vector_border)
                self._draw_str(y, width - 1, vector_border)

            self._draw_str(height - 1, 0, horizon_border)

            # draw inner content
            inner_height = height - 2
            inner_width = width - 2
            if inner_height > 0 and inner_width > 0:
                content_area = self._inner_area(
                    Rect.from_dimensions(1, 1, inner_height, inner_width)
                )
                self.__content(content_area)

        except Exception:
            pass


class Noising(ScreenElement):
    """Base class for noising components.

    Currently we use the overridable '_token' to get '_noise' formatted.
    Once the package 'windows-curses' supports Python 3.14+,
    we'll transfer the formatting method to style of t-strings.
    """

    __noise: str

    def __init__(self, stdscr: curses.window, area: Rect, noise: str) -> None:
        super().__init__(stdscr, area)
        self.__noise = noise

    def draw(self) -> None:
        """Draw the noises."""
        height, width = self._size

        token = self._token
        len_token = len(token)
        if len_token == 0:
            line = " " * width
        else:
            ratio = width // len_token
            repeats = ratio if width % len_token == 0 else ratio + 1
            line_repeated = token * repeats
            line = line_repeated if width % len_token == 0 else line_repeated[:width]

        for y in range(0, height):
            self._draw_str(y, 0, line)

    @property
    def _noise(self) -> str:
        """Return the main noise text used for filling the noising area."""
        return self.__noise

    @property
    @abstractmethod
    def _token(self) -> str:
        """Return the exact token used for filling the noising area."""

    @classmethod
    @abstractmethod
    def token_exceeds_width(cls) -> int:
        """Indicate by how many characters the token exceeds the noise text width."""


class NoisingExpanded(Noising):
    """Fills the inner area with repeating annoying text."""

    @property
    def _token(self) -> str:
        return f"    {self._noise}"

    @classmethod
    def token_exceeds_width(cls) -> int:
        return 4


class NoisingCompressed(Noising):
    """Fills the inner area with tightly packed annoying text."""

    @property
    def _token(self) -> str:
        return f"{self._noise} "

    @classmethod
    def token_exceeds_width(cls) -> int:
        return 1


class RemainingTime(ScreenElement):
    """Displays the remaining time computed from a start and a max_seconds."""

    __rem_sec: int

    def __init__(
        self, stdscr: curses.window, area: Rect, remaining_seconds: int
    ) -> None:
        super().__init__(stdscr, area)
        require(remaining_seconds > 0, "Remaining seconds must be greater than zero")
        self.__rem_sec = remaining_seconds

    def draw(self) -> None:
        """Draw the remaining time."""
        rem_text = f"Noising time remaining: {self.__format_remaining_time()}"
        height, _ = self._size
        self._draw_str(height - 2, 0, rem_text)

    def __format_remaining_time(self) -> str:
        """Format the remaining time into a human-readable string."""
        return RemainingTime.__format_time(self.__rem_sec)

    SECONDS_DAY = 86400
    SECONDS_HOUR = 3600
    SECONDS_MINUTE = 60

    @classmethod
    def __format_time(cls, seconds: int) -> str:
        """Format seconds into a human-readable string."""
        if seconds > cls.SECONDS_DAY:
            days = seconds // cls.SECONDS_DAY
            rest = seconds % cls.SECONDS_DAY
            hh = rest // cls.SECONDS_HOUR
            mm = (rest % cls.SECONDS_HOUR) // cls.SECONDS_MINUTE
            return f"{days} days and {hh:02d}:{mm:02d}"
        elif seconds > 60:
            hh = seconds // cls.SECONDS_HOUR
            mm = (seconds % cls.SECONDS_HOUR) // cls.SECONDS_MINUTE
            return f"{hh:02d}:{mm:02d}"
        else:
            return f"{seconds}s"


class ExitHint(ScreenElement):
    """Displays an exit hint at the bottom of the screen."""

    def draw(self) -> None:
        height, _ = self._size
        self._draw_str(height - 1, 0, "Press ESC to stop")


class Monitor(ScreenElement):
    """High-level monitor that composes other screen elements.

    Parameters are passed in __init__ to mimic composable parameters.
    The draw() method is parameterless and renders the full screen.
    """

    __noise: str
    __rem_sec: int | None

    def __init__(
        self,
        stdscr: curses.window,
        area: Rect,
        noise_text: str,
        remaining_seconds: int | None,
    ) -> None:
        super().__init__(stdscr, area)

        self.__noise = noise_text
        self.__rem_sec = remaining_seconds

    def draw(self) -> None:
        """Draw the full monitor screen."""
        height, width = self._size

        # main content
        if height >= 3:
            noise = self.__noise
            draw_border = height >= 5
            width_threshold = (
                len(noise)
                + NoisingExpanded.token_exceeds_width()
                + (2 if draw_border else 0)
            )
            noising = NoisingExpanded if width >= width_threshold else NoisingCompressed
            noising_area = Rect(size=Vector2D(height - 2, width))
            if draw_border:
                self._draw_sub_in(
                    BorderBox,
                    noising_area,
                    lambda area: self._draw_sub_in(noising, area, noise),
                )
            else:
                self._draw_sub_in(noising, noising_area, noise)

        if height >= 2:
            # remaining time
            rem_sec = self.__rem_sec
            if rem_sec is not None:
                self._draw_sub(RemainingTime, rem_sec)

        if height >= 1:
            # last line: exit hint
            self._draw_sub(ExitHint)
