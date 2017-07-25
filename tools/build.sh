#!/usr/bin/env sh

set -e

if [ -n $1 ] && [ "$1" = '-b' ]; then
    tools/regenerate_basic_files.sh
fi

# Create .inf files in case the files are missing those.
# Also, rename the BOOT1 file as BOOT when it gets added to the UEF file.
python -c '
open("build/BOOT1.inf", "w").write("$.BOOT 1400 8023 %x" % len(open("build/BOOT1").read()))
open("build/FASTD.inf", "w").write("$.FASTD e00 e00 %x" % len(open("build/FASTD").read()))
open("build/MENU.inf", "w").write("$.MENU 1400 8023 %x" % len(open("build/MENU").read()))
'

tools/regenerate_sutils.sh
#tools/rebuild_uef.sh
tools/make_rom.py
