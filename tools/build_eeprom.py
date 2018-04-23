#!/usr/bin/env python

"""
Copyright (C) 2017 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from cStringIO import StringIO
import os, struct, sys

class Index:

    def __init__(self):
    
        self.entries = []
        self.menu_start = 0
        self.menu_length = 0
        self.space = 0
    
    def read(self, path):
    
        f = open(path, "rb")
        if f.read(2) != "\x17\xa3":
            raise IOError("Not a Mega Games Cartridge index file: '%s'" % path)
        
        total = ord(f.read(1))
        self.menu_start = struct.unpack(">H", f.read(2))[0]
        self.menu_length = struct.unpack(">H", f.read(2))[0]
        self.space = ord(f.read(1))
        
        self.entries = []
        while len(self.entries) < total:
        
            entry = Entry(fh = f)
            self.entries.append(entry)
        
        f.close()
    
    def write(self, path = None, fh = None):
    
        if fh == None:
            fh = open(path, "wb")
        
        fh.write("\x17\xa3")
        
        fh.write(chr(len(self.entries)))
        fh.write(struct.pack(">H", self.menu_start))
        fh.write(struct.pack(">H", self.menu_length))
        fh.write(chr(self.space))
        
        for i, entry in enumerate(self.entries):
            entry.write(fh)
        
        fh.write("." * (0x4000 - fh.tell()))
        
        if path != None:
            fh.close()


class Choice:

    def __init__(self, value = None, fh = None):
    
        self.value = value
        if fh != None:
            self.read(fh)
    
    def __repr__(self):
        return self.value
    
    def read(self, fh):
    
        value = ord(fh.read(1))
        self.value = self.choices[value]
    
    def write(self, fh):
    
        value = self.choices.index(self.value)
        fh.write(chr(value))


class Mode(Choice):

    choices = ["", "1 x 16K", "2 x 16K", "Multiple"]

class Launch(Choice):

    choices = ["ROMFS Reset", "CHAIN", "*EXEC", "*RUN", "Loader"]


class Genre(Choice):

    choices = {
        "0": "Adventure (graphics)", "1": "Adventure (text)",
        "2": "Adventure (text/graphics)", "3": "Adventure (arcade)",
        "4": "Avoid 'em", "5": "Ball Control",
        "6": "Ball Game", "7": "Bat 'n' Ball",
        "8": "Beat 'em Up", "9": "Board Game",
        "A": "Card Game", "B": "Catch 'em",
        "C": "Collect 'em Up", "D": "Driving",
        "E": "Educational", "F": "Football",
        "G": "Lunar Landing", "H": "Maze",
        "I": "Platform", "J": "Puzzle",
        "K": "Quiz", "L": "RPG",
        "M": "Run 'n' Gun", "N": "Run 'n' Jump",
        "O": "Save 'em Up", "P": "Shooter",
        "Q": "Simulation", "R": "Space",
        "S": "Sport", "T": "Strategy",
        "U": "Word Games", "V": "Traditional Games"
        }
    
    def __init__(self, key = None, fh = None):
    
        self.key = key
        Choice.__init__(self, self.choices.get(key, "N/A"), fh)
    
    def read(self, fh):
    
        key = fh.read(1)
        try:
            self.key = key
            self.value = self.choices[key]
        except KeyError:
            self.key = key
            self.value = "N/A"
    
    def write(self, fh):
    
        fh.write(self.key)


class Command:

    def __init__(self, offset = 0, length = 0, attributes = (0, 0), fh = None):
    
        self.offset = offset
        self.length = length
        self.attributes = attributes
        
        if fh != None:
            self.read(fh)
    
    def read(self, fh):
    
        self.offset = ord(fh.read(1))
        self.length = ord(fh.read(1))
        self.attributes = struct.unpack("<BB", fh.read(2))
    
    def write(self, fh):
    
        fh.write(chr(self.offset) + chr(self.length) + \
                 struct.pack("<BB", *self.attributes))


class Entry:

    def __init__(self, fh = None):
    
        if fh != None:
            self.read(fh)
    
    def __repr__(self):
    
        return "Entry(name='%s' page=%i)" % (self.name, self.page)
    
    def read(self, fh):
    
        title = fh.read(46)
        self.mode = Mode(fh = fh)
        self.page = ord(fh.read(1))
        publisher_offset = ord(fh.read(1))
        self.launch = Launch(fh = fh)
        self.command = Command(fh = fh)
        self.genre1 = Genre(fh = fh)
        self.genre2 = Genre(fh = fh)
        
        i = publisher_offset
        while i > 0:
            i -= 1
            if title[i] not in " .":
                break
        
        self.name = title[:i + 1]
        self.publisher = title[publisher_offset:]
    
    def write(self, fh):
    
        padding = 46 - len(self.name) - len(self.publisher) - 1
        title = self.name + ((padding/2) * " .")
        if padding % 2 == 1:
            title += " "
        
        title += " " + self.publisher
        fh.write(title)
        
        self.mode.write(fh)
        fh.write(chr(self.page))
        fh.write(chr(46 - len(self.publisher)))
        self.launch.write(fh)
        self.command.write(fh)
        self.genre1.write(fh)
        self.genre2.write(fh)


def make_entry(name, publisher, rom_files, genres, rest, page):

    entry = Entry()
    entry.name = name
    entry.publisher = publisher
    
    if len(rom_files) == 1:
        entry.mode = Mode(value = "1 x 16K")
    elif len(rom_files) == 2:
        entry.mode = Mode(value = "2 x 16K")
    else:
        entry.mode = Mode(value = "Multiple")
    
    entry.page = page
    
    launch = int(rest[0])
    entry.launch = Launch(value = Launch.choices[launch])
    
    if len(rom_files) > 2:
        # Games with more than 2 ROMs are encoded with a command that
        # includes two more bytes: the low and high bytes of the address
        # where the base ROM bank number of the set of ROMs is stored.
        entry.command = Command(offset = int(rest[1]), length = int(rest[2]),
            attributes = (int(rest[3]), int(rest[4])))
    else:
        entry.command = Command(offset = int(rest[1]), length = int(rest[2]))
    
    entry.genre1 = Genre(genres[0])
    entry.genre2 = Genre(genres[1])
    
    return entry


if __name__ == "__main__":

    args = sys.argv[:]
    split = False
    verbose = False
    
    if "-s" in args:
        args.remove("-s")
        split = True
    
    if "-v" in args:
        args.remove("-v")
        verbose = True
    
    if split and len(args) == 6:
        choices, menu_rom_file, roms_dir = args[1:4]
        output_files = args[4:]
    elif not split and len(args) == 5:
        choices, menu_rom_file, roms_dir = args[1:4]
        output_files = args[4:]
    else:
        sys.stderr.write("\nUsage: %s <choices CSV file> <Menu ROM> <ROMs directory> "
            "<output EEPROM file>\n"
            "Create an EEPROM image based on the choices in the CSV file and using "
            "the ROMs from the given ROMs directory.\n\n" % sys.argv[0])
        sys.stderr.write("Usage: %s <choices CSV file> <Menu ROM> <ROMs directory> "
            "-s <output EEPROM file 1> <output EEPROM file 2>\n"
            "As above but writes a copy of the first EEPROM image with the upper "
            "and lower banks switched.\n"
            "These can be used as large individual ROM images in my fork of Elkulator.\n\n" % sys.argv[0])
        sys.exit(1)
    
    menu_rom = open(menu_rom_file, "rb").read()
    
    # Collect single and double ROM sets.
    rom_sets = {1: [], 2: [], 3: []}
    
    for line in open(choices).readlines():
    
        pieces = filter(lambda x: x, line.strip().split(","))
        
        name, publisher = pieces[:2]
        rom_files = []
        
        i = 2
        while i < len(pieces):
            if pieces[i].endswith(".rom"):
                rom_files.append(pieces[i])
                i += 1
            else:
                break
        
        genres = pieces[i:i+2]
        rest = pieces[i+2:]
        
        rom_sets[min(len(rom_files), 3)].append((name, publisher, rom_files, genres, rest))
    
    # Assign ROM files to banks in the EEPROM.
    banks = {}
    entries = {}
    r = 1
    
    for name, publisher, rom_files, genres, rest in rom_sets[2]:
    
        # Pairs of ROMs can only be assigned up to the 128th ROM (the index).
        if r >= 128:
            sys.stderr.write("Ran out of space while assigning ROM file "
                "'%s'.\n" % rom_files[0])
            sys.exit(1)
        
        # Create an index entry.
        entries[(name, publisher)] = make_entry(name, publisher, rom_files, genres, rest, r)
        
        banks[r] = rom_files[0]
        banks[r + 128] = rom_files[1]
        r += 1
    
    # Store collections of 3 or more ROMs sequentially.
    r = 1
    
    for name, publisher, rom_files, genres, rest in rom_sets[3]:
    
        while r < 256:
        
            # See if there is a gap large enough for all the ROM files.
            i = 0
            while i < len(rom_files) and (r + i) != 128 and \
                  (r + i) < 256 and  (r + i) not in banks:
                i += 1
            
            # If so then stop looking.
            if i == len(rom_files):
                break
            
            r += 1
        else:
            sys.stderr.write("Ran out of space while assigning ROM file "
                "'%s'.\n" % rom_files[0])
            sys.exit(1)
        
        # Create an index entry.
        entries[(name, publisher)] = make_entry(name, publisher, rom_files, genres, rest, r)
        
        i = 0
        while i < len(rom_files):
            banks[r] = rom_files[i]
            i += 1
            r += 1
    
    # Fill the gaps in the EEPROM with single ROMs.
    r = 1
    
    for name, publisher, rom_files, genres, rest in rom_sets[1]:
    
        while r in banks or r == 128:
            r += 1
        
        if r >= 256:
            sys.stderr.write("Ran out of space while assigning ROM file "
                "'%s'.\n" % rom_files[0])
            sys.exit(1)
        
        # Create an index entry.
        entries[(name, publisher)] = make_entry(name, publisher, rom_files, genres, rest, r)
        
        banks[r] = rom_files[0]
        r += 1
    
    # Construct the index with the sorted entries.
    ind = Index()
    ordered = entries.keys()
    ordered.sort()
    
    for pair in ordered:
        ind.entries.append(entries[pair])
    
    if verbose:
        ordered = banks.items()
        ordered.sort()
        for n, name in ordered:
            print n, name
    
    # Write the index to a string.
    io = StringIO()
    ind.write(fh = io)
    io.seek(0)
    idx = io.read()
    
    # Create the output EEPROMs.
    f = open(output_files[0], "wb")
    f.write(menu_rom)
    
    blank_rom = "\xff" * 16384
    i = 1
    unused = 0
    
    while i < 256:
    
        if i == 128:
            f.write(idx)
        
        elif i in banks:
            rom = open(os.path.join(roms_dir, banks[i]), "rb").read()
            f.write(rom)
        
        else:
            unused += 1
            f.write(blank_rom)
        
        i += 1
    
    f.close()
    
    print "Written %s with %i unused banks." % (output_files[0], unused)
    
    if split:
    
        f = open(output_files[0], "rb")
        g = open(output_files[1], "wb")
        
        # Swap the two halves of the first ROM file and write them to the second
        # ROM file.
        f.seek(128 * 16384)
        g.write(f.read(128 * 16384))
        f.seek(0)
        g.write(f.read(128 * 16384))
        
        f.close()
        g.close()
        
        print "Written %s with the last 128 banks first." % output_files[1]
    
    sys.exit()
