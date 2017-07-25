#!/usr/bin/env sh

set -e

# Create .inf files in case the files are missing those.
# Also, rename the BOOT1 file as BOOT when it gets added to the UEF file.
python -c '
open("build/FASTD.inf", "w").write("$.FASTD e00 e00 %x" % len(open("build/FASTD").read()))
'

UEFtrans.py mgc.uef new Electron 0
UEFtrans.py mgc.uef append build/BOOT1
UEFtrans.py mgc.uef append build/FASTD
UEFtrans.py mgc.uef append build/MENU
UEFtrans.py mgc.uef append build/SUTILS
UEFtrans.py mgc.uef append build/SCODE
