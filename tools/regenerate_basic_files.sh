#!/usr/bin/env sh

set -e

# This tool requires that UEFtrans.py, SSD2UEF.py and elkulator are on the PATH.

tools/prepare_boot.py
tools/prepare_menu.py

UEFtrans.py temp.uef new Electron 0
UEFtrans.py temp.uef append BOOT1
UEFtrans.py temp.uef append MENU

dd if=/dev/zero of=transfer.ssd bs=1024 count=200
echo "In Elkulator, copy the BOOT1 and MENU files to disk, like this:"
echo "*TAPE"
echo "*EXEC BOOT1"
echo "*DISK"
echo 'SAVE "BOOT1"'
echo "NEW"
echo "*TAPE"
echo "*EXEC MENU"
echo "*DISK"
echo 'SAVE "MENU"'
elkulator -tape temp.uef -disk transfer.ssd

UEFtrans.py temp.uef new Electron 0
SSD2UEF.py transfer.ssd temp.uef
UEFtrans.py temp.uef extract 0,1 temp
cp temp/BOOT1 build/BOOT1
cp temp/MENU build/MENU

echo "Cleaning up temporary files."
rm transfer.ssd temp.uef
rm -r temp
rm BOOT1 MENU BOOT1.inf MENU.inf
