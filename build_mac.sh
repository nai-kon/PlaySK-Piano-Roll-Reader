#! /bin/zsh
set -euo pipefail

# build cython code
pushd ./src/cis_decoder/
python setup.py build_ext --inplace
popd

# build exe
pyinstaller build_mac.spec -y

# remove temp folder
rm -rf 'dist/PlaySK Piano Roll Reader/'

# generate 3rd party license txt
pip-licenses --format=plain-vertical --with-license-file --no-license-path --output-file="3rd-party-license.txt"

# copy files
cp -p "3rd-party-license.txt" dist/
cp -p "docs/How to use.png" dist/
cp -pr src/playsk_config/ dist/playsk_config/