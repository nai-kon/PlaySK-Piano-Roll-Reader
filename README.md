# PlaySK Piano Roll Reader       
### Optically Reading a Piano Roll Scroll, Converts to Midi.

![Overall System](./README_img/Overall_System.png)

- Software Download Link  
https://drive.google.com/open?id=1NLd62Rn1izBsKbRlS4x6tuYE4-IxiKIE


- [Demo] Reading Duo-Art roll with VST Piano   
https://www.youtube.com/watch?v=qQDl1Rn39J0
 

- [Demo] Reading Ampico A roll with Yamaha Disklavier     
https://www.youtube.com/watch?v=UzccJrikBEE

This software reads piano roll scroll captured by Webcam or Video File. The Virtual Tracker Bar calculates brightness of each hole. The brightness will be darker if roll hole passes the tracker hole, it activates the note-on signal. 

The software is designed for "reading" a piano roll, not for "scanning or storage" a piano roll. If you are considering storage, hardware scanner such as "MK4 scanner" would be better. 

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
    e.x. Yamaha Disklavier, Piano VST (Ivory serires)
    
- Roll Tracking     
    -Manual Tracking (WebCam, VideoFile Input)   
    -Tracking Save function (VideoFile Input)     
     This function is save the manual tracking operation. It tracks roll automatically after recoding the manual tracking.

## Code Layout
The code is written in C/C++ Win32API, OpenCV without GUI Framework.  
I know should rewrite by using GUI Framework such as .Net, but no time for it.

My Build Environment    
-Windows 7 SP1 64bit    
-Visual Studio 2017      
-OpenCV 2.4.8 

- \MyReader   
MyReader.cpp - main souce. UI control, emulating thread       
mycv.cpp - convert opencv image to device context   
player.cpp - 88-note player class(base class)       
DuoArt.cpp - Duo-Art player class     
AmpicoA.cpp - Ampico A player class

- \ConfigFile     
88-Note.txt - 88-note tracker hole position     
Duo-Art.txt - Duo-Art tracker hole position, velocity file
Ampico_A.txt - Ampico A tracker hole position, velocity file       
Setting.ini - Global setting of the Software

- \OpenCV_248_Libs     
bin\     
include\     
lib\     

    Important : Download OpenCV 2.4.8 and locate include, lib, bin, here.       
    (I don't uploaded to GitHub)

- PostBuildEvent.bat      
Exec copy ConfigFile and OpenCV dlls to Release/Debug Folder, after building.


## How to Play

### 1. Select Midi-Out and TrackerBar, Video Source

Run PlaySK Piano Roll Reader.exe.

![Player Setting](README_img/Player_Setting.png)    
- Player Setting      
Select Midi-Out Device and Virtual Tracker Bar.

- Input Video     
-Webcam Input - Click "Webcab" and "OK"      
-VideoFile Input - Click "Video File" and select a video file.      

    At Webcam Input, default Device Number is "0".     
For changing, modify the WebCamDevNo of "Setting.ini"      
```
WebCamDevNo = 0
```
### 2. Start Reading and Emulating

![Main U I](README_img/MainUI.png)  
Click "Play" for Emulating.     

- Adjust the Tracker Hole Position    
The hole position are written on player file (88-Note.txt, Ampico_A.txt, Duo-Art.txt)
You can simplly modify note position(pixel unit). 
```
# 83 NOTES POSITION
59
66
...
570
```
- Semi Automatic Tracking (Tracking Save)     
Prepareing...
