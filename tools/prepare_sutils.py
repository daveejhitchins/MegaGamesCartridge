#!/usr/bin/env python

import os, stat, struct, sys

load_address = 0x1d00
exec_address = 0x1d00

def address_bytes(address):

    l = []
    for i in range(4):
        l.append(address & 0xff)
        address = address >> 8
    
    return tuple(l)


def main(files):

    f = open("asm/sutils-extra.oph", "w")
    
    # A list of file blocks must be written first.
    
    for file_name in files:
    
        data = open(file_name, "rb").read()
        name = os.path.split(file_name)[1].upper()
        
        f.write('.byte <%s_name, >%s_name\n' % (name, name))
        f.write('.byte $%02x, $%02x, $%02x, $%02x\n' % address_bytes(load_address))
        f.write('.byte $%02x, $%02x, $%02x, $%02x\n' % address_bytes(exec_address))
        f.write('.byte <%s_data, >%s_data, 0, 0\n' % (name, name))
        f.write('.byte <%s_data_end, >%s_data_end, 0, 0\n' % (name, name))
        
        f.write('%s_data:\n' % name)
        i = 0
        while i < len(data):
            bytes = data[i:i+16]
            f.write(".byte " + ",".join(map(str, map(ord, bytes))) + "\n")
            i += 16
        
        f.write('%s_data_end:\n\n' % name)
    
    # Add a null byte after the items to indicate the end of the list.
    f.write('.byte 0\n')
    
    f.write("\n")
    
    # Write the names of the files last.
    
    for file_name in files:
    
        name = os.path.split(file_name)[1].upper()
        f.write('%s_name:\n' % name)
        f.write('.byte "%s", 13,255\n' % name)
    
    f.close()


if __name__ == "__main__":

    if len(sys.argv) < 5:
        sys.stderr.write("Usage: %s files...\n" % sys.argv[0])
        sys.stderr.write("The files should be paths to ROMLOAD, SECWIPE, SECPROG and VUROM.\n")
        sys.exit(1)
    
    files = sys.argv[1:]
    files.sort()
    
    program = ["*RUN SCODE"]
    
    f = open("build/sutils", "wb")
    n = 10
    
    for line in program:
    
        f.write(struct.pack(">BHB", 0x0d, n, 4 + len(line)) + line)
        n += 10
    
    f.write("\r" + "\xff")
    f.close()
    
    main(files)
    sys.exit()
