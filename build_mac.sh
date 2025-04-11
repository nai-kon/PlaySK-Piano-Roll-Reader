#! /bin/zsh
set -euo pipefail

# build cython code
pushd ./src/cis_decoder/
uv run python setup.py build_ext --inplace
popd

# build exe
uv run pyinstaller build_mac.spec -y

# remove temp folder
rm -rf 'dist/PlaySK Piano Roll Reader/'

# generate 3rd party license txt
uv run pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file="3rd-party-license.txt"

# copy files
cp -p "3rd-party-license.txt" dist/
cp -p "assets/How to use Mac.png" dist/
cp -pr src/playsk_config/ dist/playsk_config/
cp -p "assets/Aeolian_176note_MIDI_setting.html" dist/