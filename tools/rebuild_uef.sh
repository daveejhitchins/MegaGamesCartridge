#!/usr/bin/env sh

set -e

UEFtrans.py mgc.uef new Electron 0
UEFtrans.py mgc.uef append build/BOOT1
UEFtrans.py mgc.uef append build/FASTD
UEFtrans.py mgc.uef append build/MENU
UEFtrans.py mgc.uef append build/SUTILS
UEFtrans.py mgc.uef append build/SCODE
