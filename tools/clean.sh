#!/usr/bin/env sh

set -e

# Ensure that we are being run in the right directory.
if [ -e asm ] && [ -e build ] && [ -e tools ] && [ -e rom_tools ]; then

    if [ -e asm/sutils-extra.oph ]; then
        rm asm/sutils-extra.oph
    fi

    if [ -e mgcmenu.rom ]; then
        rm mgcmenu.rom
    fi

    for name in [ "BOOT1" "MENU" "SUTILS" "SCODE" ]; do
        if [ -e build/$name ]; then
            rm build/$name
        fi
        if [ -e build/$name.inf ]; then
            rm build/$name.inf
        fi
    done

    for name in [ "Boot1" "Boot1.inf" "Menu" "Menu.inf" ]; do
        if [ -e $name ]; then
            rm $name
        fi
    done
fi
