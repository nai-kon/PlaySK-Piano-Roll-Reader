# PlaySK Piano Roll Reader       
### Optically Reading a Piano Roll Scroll, Converts to Midi.

This software reads piano roll scroll captured by Webcam or Video File. The Virtual Tracker Bar calculates brightness of each hole. The brightness will be darker if roll hole passes the tracker hole, it activates the note-on signal. 

The software is designed for "reading" a piano roll, not for "scanning or storage" a piano roll. If you are considering storage, hardware scanner such as SaMK4 scanner would be better. 

## Specific
- Virtual Tracker Bar   
    -Standard 88-note    
    -Duo-Art     
    -Ampico A

    Note: Song Roll couldn't read well because of printed lyrics.

- Input     
    -WebCam  (640x480, for real-time reading)    
    -Video File (640x480, over 60fps recommended)

- Output    
    -Midi Signal to Selected Midi Device    
    e.x. Yamaha Disklavier, Piano VST(Ivory serires)
    
- Roll Tracking     
    -Manual Tracking (WebCam, VideoFile Input)   
    -Tracking Save function (VideoFile Input)     
     This function is save the manual tracking operation. It tracks roll automatically after recoding the manual tracking.

## 

## Code Layout
The code is written in C/C++ Win32API, OpenCV.  
I know should rewrite by using GUI Framework such as .Net, but no time for it.

MyReader.cpp - main souce. UI control, reading thread       
mycv.cpp - convert opencv image to device context   
player.cpp - 88-note player class(base class)       
DuoArt.cpp - Duo-Art player class     
AmpicoA.cpp - Ampico A player class

* Build Environment     
-Visual Studio 2017      
-OpenCV 2.4.8       