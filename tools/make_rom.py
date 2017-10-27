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

# Based on UEF2ROM.py, UEFfile.py and the distance_pair.py compression module.

import commands, os, stat, struct, sys, tempfile

def compress(data, offset_bits = 4, window = "output"):

    max_offset = (1 << offset_bits) - 1
    max_length = (1 << (7 - offset_bits)) + 2
    
    special = find_least_used(data)
    output = [special]
    
    i = 0
    while i < len(data):
    
        best = []
        b = 0
        
        # Compare strings in the window with upcoming input, starting at the
        # beginning of the window.
        if window == "output":
            k = max(0, i - 128)
            end = i
        else:
            k = max(0, len(output) - 128)
            end = len(output)
        
        while k < end:
        
            if window == "output":
                match = find_match(data, k, i)
            else:
                match = find_match_in_compressed(output, data, k, i)
            
            # Find better matches, replacing those of equal length with later
            # ones as they are found.
            if len(match) >= len(best):
                best = match
                b = k
            
            k += 1
        
        length = len(best)
        
        if length <= 2:
        
            # If there is no match, or the match would be inefficient to record,
            # then just include the next byte in the window.
            
            # If the special byte occurs in the input, encode it using a
            # special sequence.
            if data[i] == special:
                output += [special, 0]
                i += 1
            else:
                output.append(data[i])
                i += 1
        
        else:
            # Otherwise, encode the special byte, offset from the end of the
            # window and length, skipping the corresponding number of matching
            # bytes in the input stream. Subtracting 3 from the length in the
            # second case but nothing from the offset avoids the possibility of
            # encoding a zero in the second byte, confusing the first two cases.
            #
            # special 0                 -> special
            #
            # Near references are defined using the number of bits passed in
            # the offset_bits parameter. These vary from 2 to 5:
            #
            # special 0llllloo          -> length (3-34), offset (1-3)
            # special 0llllooo          -> length (3-18), offset (1-7)
            # special 0llloooo          -> length (3-10), offset (1-15)
            # special 0llooooo          -> length (3-6), offset (1-31)
            #
            # Far references:
            # special 1ooooooo llllllll -> offset (1-128), length (4-259)
            
            if window == "output":
                offset = i - b
            else:
                offset = len(output) - b
            
            if length <= max_length and offset <= max_offset:
                # Store non-zero offset to avoid potential encoding of zero
                # in the second byte.
                output += [special, ((length - 3) << offset_bits) | offset]
                i += length
            
            elif length > 3:
                # Store offset - 1 and length - 4 to allow higher lengths
                # to be stored.
                output += [special, 0x80 | (offset - 1), length - 4]
                i += length
            
            elif data[i] == special:
                output += [special, 0]
                i += 1
            
            else:
                output.append(data[i])
                i += 1
    
    return output


def find_least_used(data):

    freq = [0] * 256
    
    for b in data:
        freq[b] += 1
    
    try:
        # Try to find an unused byte value.
        special = freq.index(0)
    except ValueError:
        # Find the least used byte value.
        pairs = map(lambda i: (freq[i], i), range(len(freq)))
        pairs.sort()
        special = pairs.pop(0)[1]
    
    return special


def find_match(data, k, i):

    # Compare the bytes in the window, starting at index k, with the bytes in
    # the upcoming data, starting at index i.
    #
    # | data   i        |
    #          v
    # | window |        |
    #   ^           ^
    #   k --------- j
    
    match = []
    j = i
    
    while len(match) < 259:
    
        if j == len(data) or data[k] != data[j]:
            return match
        
        match.append(data[k])
        
        k += 1
        j += 1
    
    return match


def find_match_in_compressed(output, data, k, i):

    # Compare the bytes in the compressed data, starting at index k, with the
    # bytes in the upcoming data, starting at index i.
    #
    #          i
    # | data   |    ^   |
    #     k ------- j
    #     v
    # | output |
    
    match = []
    j = i
    
    while len(match) < 255 and k < len(output):
    
        if j == len(data) or output[k] != data[j]:
            return match
        
        match.append(output[k])
        
        k += 1
        j += 1
    
    return match


# Each compressed file entry is
#   trigger address (2) + source address (2) + destination address (2)
# + destination end address (2) + count mask (1) + offset bits (1) = 10
compressed_entry_size = 10

class AddressInfo:

    def __init__(self, name, addr, src_label, decomp_addr, decomp_end_addr,
                       offset_bits):
    
        self.name = name
        self.addr = addr
        self.src_label = src_label
        self.decomp_addr = decomp_addr
        self.decomp_end_addr = decomp_end_addr
        self.offset_bits = offset_bits

class Block:

    def __init__(self, data, info):
        self.data = data
        self.info = info

class Compressed(Block):

    def __init__(self, data, info, raw_length, offset_bits):
        Block.__init__(self, data, info)
        self.raw_length = raw_length
        self.offset_bits = offset_bits

def format_data(data):

    s = ""
    i = 0
    while i < len(data):
        s += ".byte " + ",".join(map(lambda c: "$%02x" % ord(c), data[i:i+24])) + "\n"
        i += 24
    
    return s

def read_inf(file_name):

    name, load, exec_, length = open(file_name).read().strip().split()
    if name.startswith("$."):
        name = name[2:]
    
    return name, int(load, 16), int(exec_, 16), int(length, 16)

def rol(n, c):

    n = n << 1

    if (n & 256) != 0:
        carry = 1
        n = n & 255
    else:
        carry = 0

    n = n | c

    return n, carry


def crc(s):

    high = 0
    low = 0

    for i in s:

        high = high ^ ord(i)

        for j in range(0,8):

            a, carry = rol(high, 0)

            if carry == 1:
                high = high ^ 8
                low = low ^ 16

            low, carry = rol(low, carry)
            high, carry = rol(high, carry)

    return high | (low << 8)

def write_block(name, load, exec_, data, n, flags, address):

    out = "*"+name[:10]+"\000"
    out = out + struct.pack("<I", load)
    out = out + struct.pack("<I", exec_)
    out = out + struct.pack("<H", n)
    out = out + struct.pack("<H", len(data))
    out = out + struct.pack("<B", flags)
    out = out + struct.pack("<I", address)
    out = out + struct.pack("<H", crc(out[1:]))
    
    if data:
        out = out + data
        out = out + struct.pack("<H", crc(data))
    
    return out

def convert_files(files, decomp_addrs, data_address, header_file, details, rom_file):

    encoded_files = []
    names = []
    
    for name in files:
    
        data = open(os.path.join("build", name), "rb").read()
        name, load, exec_, length = read_inf(os.path.join("build", name + ".inf"))
        encoded_files.append((name, load, exec_, data))
    
    # Insert a !BOOT file at the start.
    temp_boot_file = "boot.tmp"
    
    if os.system("ophis -o " + commands.mkarg(temp_boot_file) + " " + \
        commands.mkarg("asm/file_boot_code.oph")) != 0:
        sys.exit(1)
    
    boot_code = open(temp_boot_file, "rb").read()
    os.remove(temp_boot_file)
    
    encoded_files.insert(0, ("!BOOT", 0x1900, 0x1900, boot_code))
    decomp_addrs.insert(0, "x")
    
    # Obtain the indices of all files.
    indices = range(len(encoded_files))
    
    roms = []
    files = []
    file_addresses = []
    blocks = []
    
    # Start adding files to the first ROM at the address following the code.
    address = data_address
    end_address = 0xc000
    
    # Create a list of trigger addresses.
    triggers = []
    
    # Examine the files at the given indices in the UEF file.
    
    for i, index in enumerate(indices):
    
        if decomp_addrs:
            decomp_addr = decomp_addrs.pop(0)
        else:
            decomp_addr = None
        
        if decomp_addr != "x":
        
            # When compressing, for all files other than the initial boot file,
            # insert a header with no block data into the stream followed by
            # compressed data and skip all other blocks in the file.
            
            name, load, exec_, raw_data = encoded_files[index]
            load = load & 0xffff
            
            this = 0
            
            while raw_data:
            
                # Create a block with only a header and no data.
                info = (name, load, exec_, "", this, 0x80)
                header = write_block(name, load, exec_, "", this, 0x80, 0)
                
                # Compress the raw data.
                compression_results = []
                
                for compress_offset_bits in range(3, 8):
                    cdata = "".join(map(chr, compress(map(ord, raw_data),
                        offset_bits = compress_offset_bits)))
                    
                    l = len(cdata)
                    if compression_results and l > compression_results[0][0]:
                        break
                    
                    compression_results.append((l, cdata, compress_offset_bits))
                
                compression_results.sort()
                cdata, compress_offset_bits = compression_results[0][1:]
                print "Compressed %s from %i to %i bytes with %i-bit offset at $%x." % (repr(name)[1:-1],
                    len(raw_data), len(cdata), compress_offset_bits, load)
                
                # Calculate the space between the end of the ROM and the
                # current address, leaving room for an end of ROM marker.
                remaining = end_address - address - 1
                
                if remaining < len(header) + compressed_entry_size + len(cdata):
                
                    # The file won't fit into the current ROM. Either put it in a
                    # new one, or split it and put the rest of the file there.
                    print "File %s won't fit in the current ROM - %i bytes too long." % (
                        repr(name), len(header) + compressed_entry_size + len(cdata) - remaining)
                    sys.exit(1)
                
                else:
                    # Reserve space for the ROM address, decompression start
                    # and finish addresses, source address and compressed data.
                    end_address -= compressed_entry_size + len(cdata)
                    
                    if this == 0:
                        file_addresses.append(address)
                    
                    blocks.append(Compressed(cdata, info, len(raw_data),
                                  compress_offset_bits))
                    triggers.append(address + len(header) - 1)
                    
                    address += len(header)
                    raw_data = ""
            
            files.append(blocks)
            blocks = []
            
            # Examine the next file.
            continue
    
        # For uncompressed data, handle each block from the file separately.
        
        name, load, exec_, raw_data = encoded_files[index]
        
        i = 0
        this = 0
        while i < len(raw_data):
        
            block_data = raw_data[i:i + 256]
            i += 256
            
            last = (i >= len(raw_data))
            flags = {True: 0x80, False: 0}[last]
            
            # Encode the full header and data, or continuation byte and data.
            if this == 0 or last:
                # The next block follows the normal header and block data.
                block = write_block(name, load, exec_, block_data, this, flags, address)
            else:
                # The next block follows the continuation marker, raw block data
                # and the block checksum.
                block = "\x23" + block_data + struct.pack("<H", crc(block_data))
            
            if this == 0:
                file_addresses.append(address)
            
            if address + len(block) > end_address - 1:
            
                # The block won't fit into the current ROM. Start a new one
                # and add it there along with the other blocks in the file.
                print "Block $%x in %s won't fit in the current ROM." % (this, repr(name))
                sys.exit(1)
            
            address += len(block)
            info = (name, load, exec_, block_data, this, flags)
            blocks.append(Block(block, info))
            
            this += 1
        
        files.append(blocks)
        blocks = []
        
        end = load + (this * 256) + len(block_data)
    
    if blocks:
        files.append(blocks)
    
    if files:
        # Record the address of the byte after the last file.
        file_addresses.append(address)
        rom = (files, file_addresses, triggers)
    
    # Write the source for the ROM file, containing the appropriate ROM header
    # and the files it contains in its ROMFS structure.
    
    tf, temp_file = tempfile.mkstemp(suffix=os.extsep+'oph')
    os.write(tf, header_file)
    
    files, file_addresses, triggers = rom
    
    # Discard the address of the first file.
    address = file_addresses.pop(0)
    
    first_block = True
    file_details = []
    
    for blocks in files:
    
        file_name = ""
        load_addr = 0
        length = 0
        
        for b, block_info in enumerate(blocks):
        
            name, load, exec_, block_data, this, flags = block_info.info
            length += len(block_data)
            last = (b == len(blocks) - 1) and block_info.data[0] != "\x23"
            
            if isinstance(block_info, Compressed):
            
                os.write(tf, "; %s %x\n" % (repr(name)[1:-1], this))
                
                next_address = file_addresses.pop(0)
                file_details.append((name, load, block_info))
                length = 0
                
                data = write_block(name, load, exec_, block_data, this, flags, next_address)
                os.write(tf, format_data(data))
                
                print " %s starts at $%x and ends at $%x, next file at $%x" % (
                    repr(name), address, address + len(data),
                    next_address)
            
            elif this == 0 or last or first_block:
                os.write(tf, "; %s %x\n" % (repr(name)[1:-1], this))
                
                if last:
                    next_address = file_addresses.pop(0)
                    block_info.raw_length = length
                    length = 0
                    
                    if this == 0:
                        print " %s starts at $%x and ends at $%x, next file at $%x" % (
                            repr(name), address, address + len(block_info.data),
                            next_address)
                
                elif this == 0:
                    file_name = name
                    load_addr = load
                    next_address = file_addresses[0]
                    print " %s starts at $%x, next file at $%x" % (
                        repr(name), address, next_address)
                
                else:
                    next_address = file_addresses[0]
                    print " %s continues at $%x, next file at $%x" % (
                        repr(name), address, next_address)
                
                first_block = False
                
                data = write_block(name, load, exec_, block_data, this, flags, next_address)
                os.write(tf, format_data(data))
            
            else:
                os.write(tf, "; %s %x\n" % (repr(name)[1:-1], this))
                data = block_info.data
                os.write(tf, format_data(data))
            
            address += len(data)
    
    write_end_marker(tf)
    
    # If a list of triggers was compiled, write the compressed data after
    # the ROMFS data, and write the associated addresses at the end of the
    # ROM file.
    
    if triggers:
    
        os.write(tf, "\n; Compressed data\n")
        os.write(tf, ".alias after_triggers %i\n" % (len(triggers) * 2))
        
        addresses = []
        for info in file_details:
        
            # Unpack the file information.
            name, decomp_addr, block_info = info
            
            src_label = "src_%x" % id(block_info)
            
            if decomp_addr != "x":
            
                addr = triggers.pop(0)
                decomp_addr = decomp_addr & 0xffff
                addresses.append(AddressInfo(name, addr, src_label, decomp_addr,
                    decomp_addr + block_info.raw_length, block_info.offset_bits))
                
                os.write(tf, "\n; %s\n" % repr(name)[1:-1])
                os.write(tf, src_label + ":\n")
                os.write(tf, format_data(block_info.data))
        
        #os.write(tf, "\n.alias debug %i" % (49 + roms.index(rom)))
        os.write(tf, "\ntriggers:\n")
        
        for address_info in addresses:
            if address_info.decomp_addr != "x":
                os.write(tf, ".byte $%02x, $%02x ; %s\n" % (
                    address_info.addr & 0xff, address_info.addr >> 8,
                    repr(address_info.name)[1:-1]))
        
        os.write(tf, "\nsrc_addresses:\n")
        
        for address_info in addresses:
            if address_info.decomp_addr != "x":
                os.write(tf, ".byte <%s, >%s ; source address\n" % (
                    address_info.src_label, address_info.src_label))
        
        os.write(tf, "\ndest_addresses:\n")
        
        for address_info in addresses:
            if address_info.decomp_addr != "x":
                os.write(tf, ".byte $%02x, $%02x ; decompression start address\n" % (
                    address_info.decomp_addr & 0xff,
                    address_info.decomp_addr >> 8))
        
        os.write(tf, "\ndest_end_addresses:\n")
        
        for address_info in addresses:
            if address_info.decomp_addr != "x":
                os.write(tf, ".byte $%02x, $%02x ; decompression end address\n" % (
                    address_info.decomp_end_addr & 0xff,
                    address_info.decomp_end_addr >> 8))
        
        os.write(tf, "\noffset_bits_and_count_masks:\n")
        
        for address_info in addresses:
            if address_info.decomp_addr != "x":
                offset_mask = (1 << address_info.offset_bits) - 1
                count_mask = 0xff ^ offset_mask
                os.write(tf, ".byte $%02x    ; count mask\n" % count_mask)
                os.write(tf, ".byte %i     ; offset bits\n" % address_info.offset_bits)
        
        os.write(tf, "\n")
        
        decomp_addrs = decomp_addrs[len(file_details):]
    
    os.close(tf)
    if os.system("ophis -o " + commands.mkarg(rom_file) + " " + commands.mkarg(temp_file)) != 0:
        sys.exit(1)
    
    os.remove(temp_file)
    
    print "Created", rom_file

def write_end_marker(tf):

    os.write(tf, "end_of_romfs_marker:\n")
    os.write(tf, ".byte $2b\n")

def get_data_address(header_file, rom_file):

    tf, temp_file = tempfile.mkstemp(suffix=os.extsep+'oph')
    os.write(tf, header_file)
    # Include placeholder values.
    os.write(tf, ".alias after_triggers 0\n")
    #os.write(tf, ".alias debug 48\n")
    os.write(tf, "triggers:\n")
    os.write(tf, "src_addresses:\n")
    os.write(tf, "dest_addresses:\n")
    os.write(tf, "dest_end_addresses:\n")
    os.write(tf, "offset_bits_and_count_masks:\n")
    os.write(tf, "end_of_romfs_marker:\n")
    os.close(tf)
    
    if os.system("ophis -o " + commands.mkarg(rom_file) + " " + commands.mkarg(temp_file)):
        sys.exit(1)
    
    data_address = 0x8000 + os.stat(rom_file)[stat.ST_SIZE]
    os.remove(temp_file)
    
    return data_address


def usage():
    sys.stderr.write("Usage: %s\n" % sys.argv[0])
    sys.exit(1)

if __name__ == "__main__":

    args = sys.argv[:]
    indices = []
    
    details = {
        "title": '.byte "Mega Games Cartridge", 0',
        "version string": '.byte "1.3", 0',
        "version": ".byte 1",
        "copyright": '.byte "(C) Retro Hardware", 0',
        "rom name": '.byte "MGC", 13',
        }
    
    files = ["BOOT1", "TITLE", "FASTD", "MENU", "SUTILS", "SCODE"]
    decomp_addrs = [0x1400, 0x2e00, 0xe00, 0x1400, "x", 0x1900]
    rom_file = "MENU.ROM"
    
    header_template = open("asm/romfs-template.oph").read()
    
    # Calculate the starting address of the ROM data by assembling the ROM
    # template files.
    minimal_header_template = open("asm/romfs-template.oph").read()
    
    header = header_template % details
    
    data_address = get_data_address(minimal_header_template % details, rom_file)
    
    # Convert the files to ROM data.
    convert_files(files, decomp_addrs, data_address, header, details, rom_file)
    
    length = os.stat(rom_file)[stat.ST_SIZE]
    print "%i bytes used." % length
    
    remainder = length % 16384
    if remainder != 0:
        print "Padding %s to 16K." % rom_file
        data = open(rom_file, "rb").read()
        open(rom_file, "wb").write(data + ("\xff" * (16384 - remainder))) 
    
    sys.exit()
