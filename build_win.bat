@echo off

call .venv\Scripts\activate

rem build cython code
pushd .\src\cis_decoder\
python setup.py build_ext --inplace
popd

rem build exe
pyinstaller build_win.spec
call deactivate

rem copy config files
xcopy /s /i /y .\src\config\ .\dist\config\