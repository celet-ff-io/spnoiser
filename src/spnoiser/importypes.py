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

"""Import types with proper error handling for optional dependencies."""

import sys

try:
    import curses
except Exception as e:
    print("'curses' not available:", e, file=sys.stderr)
    print(
        "Please install 'windows-curses' on Windows.",
        file=sys.stderr,
    )
    sys.exit(1)

__all__ = ["curses"]
