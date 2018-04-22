# Mega Games Cartridge

This repository contains files and tools for the menu and hardware development
of the Mega Games Cartridge by Retro Hardware.

## Building the Menu ROM

The build process is run from the command line using a shell like `bash` or
possibly `dash`. The process requires Python and the Ophis 6502 assembler.

 * Place the ready-to-use `BOOT1` and `MENU` files in the `build` directory.
   These should be the tokenized forms of the `BOOT1E` and `Menu50M` files,
   and the `MENU` file should have been crunched, squashed or otherwise
   processed so that it is much smaller than the original.
 * Place the ROM tools, `ROMLOAD`, `SECPROG`, `SECWIPE` and `VUROM` in the
   `rom_tools` directory.
 * From the root directory of the repository, run the `tools/build.sh` script.
   This should create `SUTILS` and `SCODE` files in the `build` directory and
   create a ROM file, `mgcmenu.rom`, in the repository root.

The ROM should be usable in an emulator or in a real machine.

## Editing the ROM Details

The name, copyright information and version are stored in the
`tools/make_rom.py` script. It should be fairly straightforward to change
these.

## Building a full EEPROM image

The `tools/build_eeprom.py` script can build the entire 4 MB EEPROM image from
a CSV file containing the user's choices, the menu ROM created using the
process above, and a directory of individual ROM images.

Run the script in the following way, where `choices.csv` and `/tmp/ROMs` are
examples of file and directory locations:

  tools/build_eeprom.py choices.csv MENU.ROM /tmp/ROMs /tmp/MGC.ROM

The output file - `MGC.ROM` in this case - is created and should be padded to
4 MB in size.
