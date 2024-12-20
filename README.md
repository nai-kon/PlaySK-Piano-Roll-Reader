# PlaySK Piano Roll Reader Ver3.5

Optically reading a piano roll image, emulates expression and output midi signal in real-time.

![Overall System](./assets/Overall_System.webp)

The "virtual tracker bar" optically picks up roll holes then emulates note, pedal and expression code. The expression code is decoded to vacuum level (in inches of water) in real-time, then convert to MIDI velocity.

Currently, 9 virtual tracker bars are available.
- Standard 88-note
- Ampico B
- Duo-Art
- Welte-Mignon Licensee
- Welte-Mignon T-98 (Green)
- Welte-Mignon T-100 (Red)
- Philipps Duca (no expression. experimental)
- Recordo version A / B
- Artecho
- Themodist
    - `Themodist e-Valve` supports e-valve midi note output. (18 for sustain, 19 for bass snakebite, 109 for treble snakebite)

In the future, Ampico A will be supported.

Support image formats are `.cis`, `.jpg`, `.tif`, `.png`, `.bmp`. 

`.cis` supports various scanners such as stepper, wheel/shaft encoder, bi-color, twin-array.

## Demo

- Reading an Ampico B roll with Yamaha Disklavier  
    https://www.youtube.com/watch?v=9f9J4TRmr5Y

- Reading a Red Welte T-100 roll with Software Synthesizer  
    https://www.youtube.com/watch?v=WMEPW-UWhSU

## Donation

I personally pay near $100 a year to codesign and notarize software for distribution. Your support greatly contributes to the continuous development and improvement of the Software. Please consider donating.

https://www.paypal.com/paypalme/KatzSasaki

## Usage

1. Download the software and sample scans
    https://github.com/nai-kon/PlaySK-Piano-Roll-Reader/releases/
2. Launch the program and Select MIDI output port and Virtual tracker bar
3. Select scan image from `sample_scans` folder
4. Enjoy!


## Manual Expression

If you check `☑ Manual Expression`, you can express dynamics using the keyboard.
* `J`, `K`, `L`: intensity level (can be combined)
* `A`, `S`: bass and treble accent


## Tips
* The program picks up lighted holes of image.
* Automatically set the tempo if the input filename has the tempo keyword (except .cis)
    * e.g.) `Ampico 52305 Clair de Lune tempo90.jpg` -> set the tempo to 90 automatically.
    * If no keyword is given, the default tempo is set. 98 for the Welte T-100 and 80 for the others.
* Associate the program with .cis on right-click menu, you can run app by double-clicking .cis file.
* The roll acceleration emulating is done by spool diameter and roll thickness.
* The roll scrolling direction is downward. So the Welte T-100 image should be inverted.

# For developers

## Requirements

* Python 3.11.6
* Poetry

Quick Start
```
$ poetry install
$ poetry shell
$ cd src/
$ python main.py
```

## Build binary locally

- Windows (x64)
    - `poetry run ./build_win.bat`
    - tested on Windows10
- macOS (x64/ARM)
    - `poetry run ./build_mac.sh`
    - tested on macOS Venture (both Intel and M1 cpu)


## CI/CD

There are test and release pipelines on Github Actions.
* PR or merge into main repository triggers unit tests.
* Push a tag triggers build binary and create a draft of the release. 
    * On Mac app, codesign, notarization, dmg installer creation are also triggered. (This uses my personal Apple Developer ID)

## Sequence diagram
```mermaid
sequenceDiagram
    participant user
    participant appmain
    participant update check thread
    participant image scroll thread
    participant emulator as roll view &<br>player emulation
    participant midi port

    user->>+appmain: start app
    appmain->>appmain: load last config
    appmain->>+update check thread: start update check thread
    update check thread->>appmain: 
    update check thread->>-update check thread: check update
    user->>appmain: open file
    appmain->>+image scroll thread: start image scroll thread
    image scroll thread->>appmain: 
    image scroll thread->>image scroll thread: load file
    loop over 100hz
        image scroll thread->>+emulator: roll image
        emulator->>+midi port: migi signal
        midi port->>-emulator: 
        emulator->>-image scroll thread: 
        image scroll thread->>+emulator: roll image
        emulator->>+midi port: migi signal
        midi port->>-emulator: 
        emulator->>-image scroll thread: 
    end
    user->>appmain: change tempo
    appmain->>image scroll thread: 
    image scroll thread->>image scroll thread: change scroll speed
    user->>appmain: change tracker bar
    appmain->>emulator: 
    emulator->>emulator: change tracker bar
    
    
    user->>appmain: open file
    appmain->>image scroll thread: end request
    image scroll thread->>-appmain: 
    appmain->>+image scroll thread: start image scroll thread
    image scroll thread->>image scroll thread: load file
    loop over 100hz
        image scroll thread->>+emulator: roll image
        emulator->>+midi port: migi signal
        midi port->>-emulator: 
        emulator->>-image scroll thread: 
        image scroll thread->>+emulator: roll image
        emulator->>+midi port: migi signal
        midi port->>-emulator: 
        emulator->>-image scroll thread: 
    end
    user->>appmain: select close button
    appmain->>image scroll thread: end request
    image scroll thread->>-appmain: 
    appmain->>-user: end app
```