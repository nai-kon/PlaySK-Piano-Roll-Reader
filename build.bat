@echo off

rem build
call venv\Scripts\activate.bat
pyinstaller main.spec
deactivate

rem copy config files
xcopy /s /i /y .\src\config\ .\dist\config\