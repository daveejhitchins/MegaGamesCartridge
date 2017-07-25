#!/usr/bin/env sh

set -e

tools/prepare_sutils.py build/ROMLOAD build/SECWIPE build/SECPROG build/VUROM
ophis -o build/scode asm/sutils.oph
python -c '
open("build/sutils.inf", "w").write("$.SUTILS e00 8023 %x" % len(open("build/sutils").read()))
open("build/scode.inf", "w").write("$.SCODE 1900 1900 %x" % len(open("build/scode").read()))
'
