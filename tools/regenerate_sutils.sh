#!/usr/bin/env sh

set -e

tools/prepare_sutils.py rom_tools/ROMLOAD rom_tools/SECWIPE rom_tools/SECPROG rom_tools/VUROM
ophis -o build/SCODE asm/sutils.oph
python -c '
open("build/SUTILS.inf", "w").write("$.SUTILS e00 8023 %x" % len(open("build/SUTILS").read()))
open("build/SCODE.inf", "w").write("$.SCODE 1900 1900 %x" % len(open("build/SCODE").read()))
'
