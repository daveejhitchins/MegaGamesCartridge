#!/usr/bin/env sh

set -e

if [ -n $1 ] && [ "$1" = '-b' ]; then
    tools/regenerate_basic_files.sh
fi

tools/regenerate_sutils.sh
tools/rebuild_uef.sh
