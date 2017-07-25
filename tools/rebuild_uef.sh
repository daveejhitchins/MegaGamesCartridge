#!/usr/bin/env sh

set -e

# Create .inf files in case the files are missing those.
# Also, rename the BOOT1 file as BOOT when it gets added to the UEF file.
python -c '
open("build/BOOT1.inf", "w").write("$.BOOT 1400 8023 %x" % len(open("build/BOOT1").read()))
open("build/FASTD.inf", "w").write("$.FASTD e00 e00 %x" % len(open("build/FASTD").read()))
open("build/MENU.inf", "w").write("$.MENU 1400 8023 %x" % len(open("build/MENU").read()))
'

UEFtrans.py mgc.uef new Electron 0
UEFtrans.py mgc.uef append build/BOOT1
UEFtrans.py mgc.uef append build/FASTD
UEFtrans.py mgc.uef append build/MENU
UEFtrans.py mgc.uef append build/sutils
UEFtrans.py mgc.uef append build/scode

