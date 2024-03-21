#! /bin/zsh
set -euo pipefail

# Codesign and notarize the built Mac app then create dmg file.
# This only works on author's Mac.

pushd dist

# codesign
echo "~~ codesign ~~"
IDENTITY=`security find-identity -v -p codesigning | grep "Developer ID Application"  | awk '{print $2}'`
codesign --deep --force --options=runtime --entitlements ../entitlements.plist --sign $IDENTITY \
        --timestamp "PlaySK Piano Roll Reader.app/"

# notarize & staple
echo "~~ notarize & staple ~~"
mkdir to_notarize
mv "PlaySK Piano Roll Reader.app" playsk_config to_notarize/
ditto -c -k -rsrc --keepParent to_notarize archive.zip
xcrun notarytool submit archive.zip --keychain-profile "notary_profile" --wait
mv to_notarize/* .
rm -rf to_notarize archive.zip
xcrun stapler staple "PlaySK Piano Roll Reader.app"

# create dmg
echo "~~ create dmg ~~"
test -f PlaySK-Installer.dmg && rm PlaySK-Installer.dmg
create-dmg --volname "PlaySK Installer" --background ../assets/dmg-bg.tiff \
    --window-pos 200 120 --window-size 800 500 \
    --icon-size 100 --icon "PlaySK Piano Roll Reader.app" 100 100 \
    --add-file "playsk_config" playsk_config 100 300 \
    --hide-extension "PlaySK Piano Roll Reader.app" \
    --app-drop-link 600 200 "PlaySK-Installer.dmg" "PlaySK Piano Roll Reader.app"

# archive to zip for distribution
echo "~~ archive to zip ~~"
zip -qr "PlaySK-PianoRoll-Reader-v3.2-Mac.ARM.zip" ../sample_scans/ PlaySK-Installer.dmg "How to use Mac.png" "3rd-party-license.txt"

echo "complete!"