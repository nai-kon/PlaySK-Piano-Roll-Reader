@echo off

rem Bat Args : %1 = "$(OutDir)", %2 = "$(ConfigurationName)" 
SET output_dir=%1Output\%2

rem Copy Config files to Release/Debug Dir
copy /Y %1ConfigFile\* %output_dir%.

rem Copy OpenCV binary to Release/Debug Dir
copy /Y %1OpenCV_249_Libs\bin\opencv_ffmpeg249*.dll %output_dir%.
copy /Y %1OpenCV_249_Libs\bin\%2\opencv_core249*.dll %output_dir%.
copy /Y %1OpenCV_249_Libs\bin\%2\opencv_highgui249*.dll %output_dir%.