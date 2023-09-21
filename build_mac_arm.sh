#! /bin/zsh

# build
source .venv/bin/activate
pyinstaller build_mac_arm.spec
deactivate

# remove temp file
rm 'dist/PlaySK Piano Roll Reader'

# copy config files
cp -pr src/config/ dist/config/