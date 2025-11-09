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

"""Core UI components and base classes for screen elements."""

from abc import ABC, abstractmethod
from collections import namedtuple
from dataclasses import dataclass
from typing import Callable, Concatenate, Generator, Self
from spnoiser.importypes import curses
from spnoiser.utils import require

Vector2D = namedtuple("Vector2D", ["y", "x"])
Vector2D.__annotations__ = {"y": int, "x": int}
Vector2D.__doc__ = """2D vector representing (y, x) coordinates."""


@dataclass(frozen=True, slots=True)
class Rect:
    """Represents a rectangular area on the screen."""

    offset: Vector2D = Vector2D(0, 0)
    size: Vector2D = Vector2D(0, 0)

    def __iter__(self) -> Generator[Vector2D]:
        yield self.offset
        yield self.size

    @classmethod
    def from_dimensions(cls, y: int, x: int, height: int, width: int) -> Self:
        """Create a Rect from top-left coordinates and size."""
        return cls(offset=Vector2D(y, x), size=Vector2D(height, width))

def max_area_of(stdscr: curses.window) -> Rect:
    """Get the maximum area of the given stdscr."""
    height, width = stdscr.getmaxyx()
    return Rect.from_dimensions(0, 0, height, width)


type ScreenElementFactory[**P, R] = Callable[Concatenate[curses.window, Rect, P], R]


class ScreenElement(ABC):
    """Base class for screen elements."""

    __stdscr: curses.window
    __area: Rect

    def __init__(self, stdscr: curses.window, area: Rect) -> None:
        self.__stdscr = stdscr
        self.__area = area

    @property
    def _stdscr(self) -> curses.window:
        """Get the curses standard screen window."""
        return self.__stdscr

    @property
    def _area(self) -> Rect:
        """Get the area allocated for this screen element."""
        return self.__area

    @property
    def _offset(self) -> Vector2D:
        """Get the offset of this screen element."""
        return self._area.offset

    @property
    def _size(self) -> Vector2D:
        """Get the size of this screen element."""
        return self._area.size

    @abstractmethod
    def draw(self) -> None:
        """Render the element into the stdscr."""

    def _draw_sub[T: ScreenElement, **P](
        self,
        sub_elemnt_factory: ScreenElementFactory[P, T],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        """Draw a sub-element."""
        self._draw_sub_in(sub_elemnt_factory, None, *args, **kwargs)

    def _draw_sub_in[T: ScreenElement, **P](
        self,
        sub_elemnt_factory: ScreenElementFactory[P, T],
        relative_area: Rect | None,
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        """Draw a sub-element in a specified area."""
        self_area = self._area
        target_area = (
            self_area if relative_area is None else self._inner_area(relative_area)
        )
        sub_elemnt = sub_elemnt_factory(self._stdscr, target_area, *args, **kwargs)
        sub_elemnt.draw()

    def _inner_area(self, area: Rect) -> Rect:
        """Get the inner area within this instance's area."""
        self_area = self._area
        return Rect(
            offset=Vector2D(
                self_area.offset.y + area.offset.y,
                self_area.offset.x + area.offset.x,
            ),
            size=Vector2D(
                min(self_area.size.y, area.size.y),
                min(self_area.size.x, area.size.x),
            ),
        )

    def _draw_str(
        self,
        y: int,
        x: int,
        string: str,
        *,
        on_curses_error: Callable[[curses.error], None] | None = None,
    ) -> None:
        """Draw a string at the given position, handling curses errors."""
        _, width = self._size
        try:
            self._stdscr.addstr(*self._abs_coords(y, x), string[:width])
        except curses.error as err:
            if on_curses_error is not None:
                on_curses_error(err)

    def _abs_coords(self, y: int, x: int) -> Vector2D:
        """Get absolute coordinates in stdscr for given local coordinates."""
        offset, size = self._area
        off_y, off_x = offset
        len_y, len_x = size
        require(0 <= y < len_y, "y is out of bounds")
        require(0 <= x < len_x, "x is out of bounds")
        y_abs = off_y + y
        x_abs = off_x + x
        return Vector2D(y_abs, x_abs)
