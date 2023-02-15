# PlaySK Piano Roll Reader Ver3.0

Optically reading a piano roll image, emulates expression and output midi signal in real-time.

![Overall System](./docs/Overall_System.jpg)

The "virtual tracker bar" optically picks up the roll holes then emulates note, pedal and expression.
Currently, four "virtual tracker bar" are available.
- Ampico B
- Welte-Mignon Licensee
- Welte-Mignon T-100 (Red)
- Standard 88-note

We have a plan to support Ampico A and Duo-Art in the future.

## Download binary

Windows and Mac binaries are available.

https://github.com/nai-kon/PlaySK-Piano-Roll-Reader/releases/tag/Ver3.0


## Tips
* The program picks up lighted holes. Dark holes are not supported on this version.
* The input image requires white padding on both roll edges.
* The roll scrolling direction is downward. So the Welte T-100 image should be inverted.
* Ver3.0 only supports the scanned image. WebCam and .mp4 are not supported.
* Automatically set the tempo if the input filename has the tempo keyword (tempoXX)
    * e.g.) `Ampico 52305 Clair de Lune tempo90.jpg` -> set the tempo to 90 automatically.
    * The tempo of Welte T-100 is fixed to 98.


# For developer

## Requirements
Developed with Python 3.9.13. 

Quick Start
```
$ pip install -r requirements.txt
$ cd src/
$ python main.py
```
We recommend to install on venv.

## Build binary

- Windows
    - `./build_win.bat`
    - tested on Windows10
- macOS
    - `./build_mac.sh`
    - tested on macOS Venture with Intel CPU
    - not tested on Apple silicon

## Notes
* dark mode on Windows is not working due to the wxpython.
* 

## 