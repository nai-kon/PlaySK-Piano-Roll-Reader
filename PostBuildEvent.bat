@echo off

rem Bat Args : %1 = "$(OutDir)", %2 = "$(ConfigurationName)" 
SET output_dir=%1bin\%2

rem Copy Config files to Release/Debug Dir
xcopy %1config %output_dir%\config /I /Y

rem Copy OpenCV binary to Release/Debug Dir
copy /Y %1lib_opencv_249\bin\opencv_ffmpeg249*.dll %output_dir%.
copy /Y %1lib_opencv_249\bin\%2\opencv_core249*.dll %output_dir%.
copy /Y %1lib_opencv_249\bin\%2\opencv_highgui249*.dll %output_dir%.
copy /Y %1lib_opencv_249\bin\%2\opencv_imgproc249*.dll %output_dir%.