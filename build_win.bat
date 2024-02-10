@echo off

rem build cython code
pushd .\src\cis_decoder\
python setup.py build_ext --inplace
if %errorlevel% neq 0 (
    echo failed to build cython code
    exit /b
)
popd

rem build exe
pyinstaller build_win.spec -y

rem generate 3rd party license txt
pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file="3rd-party-license.txt"

rem copy files
xcopy /i /y "3rd-party-license.txt" ".\dist\PlaySK Piano Roll Reader\"
xcopy /i /y ".\docs\How to use.png" ".\dist\PlaySK Piano Roll Reader\"
xcopy /s /i /y ".\src\playsk_config\" ".\dist\PlaySK Piano Roll Reader\playsk_config\"