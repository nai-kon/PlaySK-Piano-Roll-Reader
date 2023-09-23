#! /bin/zsh
set -euo pipefail

# build
source .venv/bin/activate

case `uname -m` in
    "x86_64" ) pyinstaller build_mac_x64.spec;;
    "arm64" ) pyinstaller build_mac_arm.spec;;
esac
deactivate

# remove temp file
rm 'dist/PlaySK Piano Roll Reader'

# copy config files
cp -pr src/config/ dist/config/