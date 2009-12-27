#!/bin/bash

pushd $(dirname $0) &>/dev/null

VOLUME_NAME=ESReader
DMG_APP=../build/Release/ESReader.app
DMG_FILE=$VOLUME_NAME.dmg
MOUNT_POINT=$VOLUME_NAME.mounted

rm -f $DMG_FILE
rm -f $DMG_FILE.master

# Compute an approximated image size in MB, and bloat by 1MB
image_size=$(du -ck $DMG_APP dmg-data | tail -n1 | cut -f1)
image_size=$((($image_size + 1000) / 1000))

echo "Creating disk image (${image_size}MB)..."
hdiutil create $DMG_FILE -megabytes $image_size -volname $VOLUME_NAME -fs HFS+ -quiet || exit $?

echo "Attaching to disk image..."
hdiutil attach $DMG_FILE -readwrite -noautoopen -mountpoint $MOUNT_POINT -quiet

echo "Populating image..."

cp -R $DMG_APP $MOUNT_POINT

pushd $MOUNT_POINT &>/dev/null
ln -s /Applications " "
popd &>/dev/null

mkdir $MOUNT_POINT/.background
cp dmg-data/background.png $MOUNT_POINT/.background
cp dmg-data/DS_Store $MOUNT_POINT/.DS_Store

echo "Detaching from disk image..."
hdiutil detach $MOUNT_POINT -quiet

mv $DMG_FILE $DMG_FILE.master

echo "Creating distributable image..."
hdiutil convert -quiet -format UDBZ -o $DMG_FILE $DMG_FILE.master

echo "Done."

if [ ! "x$1" = "x-m" ]; then
	rm $DMG_FILE.master
fi

popd &>/dev/null
