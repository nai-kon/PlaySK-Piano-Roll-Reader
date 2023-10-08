@echo off

call .venv\Scripts\activate

rem build cython code
pushd .\src\cis_decoder\
python setup.py build_ext --inplace
popd

rem build exe
pyinstaller build_win.spec -y
call deactivate

rem generate 3rd party license txt
pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file="3rd-party-license.txt"

rem copy files
xcopy /s /i /y 3rd-party-license.txt .\dist\
xcopy /s /i /y .\src\config\ .\dist\config\