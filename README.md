# PlaySK Piano Roll Reader

Optically reading a piano roll scanned image, emulates expression and output midi signal in real-time.

![Overall System](./docs/Overall_System.png)

Currently supports those player systems.

- Ampico B
- Welte-Mignon Licensee
- Welte-Mignon T-100 (Red)
- Standard 88-note

notes. The latest version only supports a scanned image input. WebCam and .mp4 are not supported.

## Environments
Developed with Python 3.9.13.

Install dependencies.

`pip install -r requirements.txt`

## Build binary

- Windows
    - `./build_win.bat`
    - tested on Windows10
- macOS
    - `./build_mac.sh`
    - tested on macOS Venture with Intel CPU
    - not tested on Apple silicon
