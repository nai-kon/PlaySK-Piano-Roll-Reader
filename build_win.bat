@echo off

rem build cython code
pushd .\src\cis_decoder\
uv run python setup.py build_ext --inplace
if %errorlevel% neq 0 (
    echo failed to build cython code
    exit /b
)
popd

rem build exe
uv run pyinstaller build_win.spec -y

rem check 3rd party license
uv run pip-licenses --partial-match --allow-only="MIT;BSD;MPL;Apache;HPND;GPLv2;Python Software;wxWindows" > nul || exit /b 1

rem generate 3rd party license txt
uv run pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file="3rd-party-license.txt"

rem copy files
xcopy /i /y "3rd-party-license.txt" ".\dist\PlaySK Piano Roll Reader\"
xcopy /i /y ".\assets\How to use.png" ".\dist\PlaySK Piano Roll Reader\"
xcopy /s /i /y ".\src\playsk_config\" ".\dist\PlaySK Piano Roll Reader\playsk_config\"
xcopy /i /y ".\assets\Aeolian_176note_MIDI_setting.html" ".\dist\PlaySK Piano Roll Reader\"