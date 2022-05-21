@echo off

rem build
pyinstaller main.spec

rem copy config files
xcopy /s /i /y .\src\config\ .\dist\config\