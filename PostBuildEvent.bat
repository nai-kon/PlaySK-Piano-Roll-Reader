@echo off

rem Bat Args : %1 = "$(SolutionDir)", %2 = "$(ConfigurationName)" 

rem Copy Config files to Release/Debug Dir
copy /Y %1ConfigFile\* %1%2.

rem Copy OpenCV binary to Release/Debug Dir
copy /Y %1OpenCV_248_Libs\bin\Win32\v120\opencv_ffmpeg248*.dll %1%2.
copy /Y %1OpenCV_248_Libs\bin\Win32\v120\%2\opencv_core248*.dll %1%2.
copy /Y %1OpenCV_248_Libs\bin\Win32\v120\%2\opencv_highgui248*.dll %1%2.