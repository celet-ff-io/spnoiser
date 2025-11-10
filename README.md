# spnoiser

Simple noiser: a tiny terminal alarm that repeats a message on the screen and can loop a short audio file (WAV recommended).

The package entry point is `spnoiser.app`. The main function accepts command-line arguments to control the displayed text, maximum duration, and an optional audio file to loop. If no audio file is provided, the program will attempt to use the terminal beep.

This project uses `src/main.py` as an alternative entrance, for debugging especially.

## Quick start

- Run directly from source:

```bash
uv run src/main.py -n "Beep" -t 120
```

- Install editable and run:

```bash
uv tool install -e .
spnoiser -n "Beep" -t 120
```

Note: the `spnoiser` console script is provided by the package entry point and is available after installation.

## Command-line arguments

The program (via `spnoiser.app:main`) supports the following options:

- `-n, --noise`  : Text to repeat on the terminal.
- `-t, --time`   : Maximum annoying time in seconds.
- `-s, --sound`  : Path to an audio file to loop. If omitted, the terminal beep is used when available.
- `-v, --volume` : Volume level for the sound file (>= 0.0). Default is 1.0.

Examples:

```bash

# Install first
uv tool install -e .

# Custom text and infinite duration, use terminal beep
spnoiser -n "Beep!" -t 0

# Loop a sound file to play instead of terminal beep
spnoiser -s "music/alarm.mp3"
```

## License

This project is licensed under the Apache License 2.0.

See the `LICENSE` file or the Apache website for the full license text: http://www.apache.org/licenses/LICENSE-2.0
