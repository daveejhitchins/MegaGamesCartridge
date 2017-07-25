#!/usr/bin/env sh

set -e

tools/prepare_boot.py
tools/prepare_menu.py

UEFtrans.py temp.uef new Electron 0
UEFtrans.py temp.uef append Boot1
UEFtrans.py temp.uef append Menu

cp templates/blank.ssd transfer.ssd
/data/david/Software/Emulation/elkulator/elkulator -tape temp.uef -disk transfer.ssd 

UEFtrans.py temp.uef new Electron 0
SSD2UEF.py transfer.ssd temp.uef
UEFtrans.py temp.uef extract 0,1 temp
cp temp/BOOT1 build/BOOT1
cp temp/MENU build/MENU

echo "Cleaning up temporary files."
rm transfer.ssd temp.uef
rm -r temp
