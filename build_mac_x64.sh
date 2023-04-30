#! /bin/zsh

# build
source venv/bin/activate
pyinstaller build_mac_x64.spec
deactivate

# remove temp file
rm 'dist/PlaySK Piano Roll Reader'

# copy config files
cp -pr src/config/ dist/config/