#!/usr/bin/env sh

set -e

tools/prepare_boot.py
tools/prepare_menu.py

~/Private/Python/UEFfile/UEFtrans.py temp.uef new Electron 0
~/Private/Python/UEFfile/UEFtrans.py temp.uef append Boot1
~/Private/Python/UEFfile/UEFtrans.py temp.uef append Menu

cp templates/blank.ssd transfer.ssd
/data/david/Software/Emulation/elkulator/elkulator -tape temp.uef -disk transfer.ssd 

~/Private/Python/UEFfile/UEFtrans.py temp.uef new Electron 0
~/Private/Python/Games/Emulation/UEF2ROM/SSD2UEF.py transfer.ssd temp.uef
~/Private/Python/UEFfile/UEFtrans.py temp.uef extract 0,1 temp
cp temp/BOOT1 build/BOOT1
cp temp/MENU build/MENU

rm transfer.ssd temp.uef
rm -r temp

python -c '
open("build/BOOT1.inf", "w").write("$.BOOT 1400 8023 %x" % len(open("build/BOOT1").read()))
open("build/MENU.inf", "w").write("$.MENU 1400 8023 %x" % len(open("build/MENU").read()))
'
