#!/usr/bin/env python

"""
Copyright (C) 2016 David Boddie <david@boddie.org.uk>

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

import os, stat, struct, sys
import Image

from palette import get_entries, black, red, green, yellow, blue, magenta, \
                    cyan, white

palette = {"\x00\x00\x00": 0,
           "\xff\x00\x00": 1,
           "\xff\xff\x00": 2,
           "\xff\xff\xff": 3}

def read_png(path):

    im = Image.open(path).convert("RGB")
    s = im.tostring()
    
    data = []
    a = 0
    
    i = 0
    while i < im.size[1]:
    
        line = []
        
        j = 0
        while j < im.size[0]:
        
            line.append(palette[s[a:a+3]])
            a += 3
            j += 1
        
        i += 1
        data.append(line)
    
    return data

def read_sprite(lines):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):
    
        width = len(lines[0])
        
        # Read 4 columns at a time.
        for column in range(0, width, 4):
        
            # Read the rows.
            for line in lines[row:row + 8]:
            
                shift = 3
                byte = 0
                for pixel in line[column:column + 4]:
                
                    if pixel == 1:
                        byte = byte | (0x01 << shift)
                    elif pixel == 2:
                        byte = byte | (0x10 << shift)
                    elif pixel == 3:
                        byte = byte | (0x11 << shift)
                    
                    shift -= 1
                
                data += chr(byte)
    
    return data

rainbow_colours = [red, yellow, green, cyan, blue, magenta]

def rainbow(i, colours, s):

    # Each physical colour is used in two adjacent rows.
    c1 = colours[(i/s) % len(colours)]
    c2 = colours[(((i+1)/s) + 1) % len(colours)]
    return [black, c1, c2, white]

def mgc_palette(full = True):

    # Special MGC title palette processing
    
    fe08_data = []
    fe09_data = []
    
    blank = get_entries(4, [black, black, black, black])
    standard = get_entries(4, [black, red, yellow, white])
    
    if full:
        s1, s2 = 111, 65
    else:
        s1, s2 = 43, 3
    
    for i in range(256):
    
        if i >= 128 + s1:
            fe08, fe09 = get_entries(4, rainbow(i - 239, [yellow, cyan, white, green, cyan], 3))
        elif i >= 128 + s2:
            fe08, fe09 = get_entries(4, rainbow(i, rainbow_colours, 3))
        elif full and i >= 128 + 46:
            fe08, fe09 = get_entries(4, rainbow(i, [white, cyan, green, yellow], 3))
        elif full and i > 128:
            fe08, fe09 = get_entries(4, [black, blue, cyan, white])
        else:
            fe08, fe09 = standard
        
        fe08_data.append(fe08)
        fe09_data.append(fe09)
    
    return fe08_data, fe09_data


if __name__ == "__main__":

    # Special MGC title image and code processing
    
    # Convert the PNG to screen data and compress it with the palette data.
    mgctitle_sprite = read_sprite(read_png("images/mgctitle.png"))
    fe08_data, fe09_data = mgc_palette(full = True)
    
    # Write the uncompressed title data to a file for other tools to use.
    open("build/TITLE", "wb").write("".join(map(chr, fe08_data + fe09_data)) + mgctitle_sprite)
