@echo off

rem build
call .venv\Scripts\activate
pyinstaller build_win.spec
call deactivate

rem copy config files
xcopy /s /i /y .\src\config\ .\dist\config\