#!/usr/bin/env python

import os, re, stat, string

text = open("Menu50M").read()
f = open("MENU", "w")

lines = []
numbers = {}
variables = set()
procedures = set()
n = 10
int_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)%")
str_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)\$")
proc_r = re.compile(r"(PROC([A-Z][a-z]+)+)")

for line in text.split("\r"):

    line = line.lstrip()
    if not line or line.startswith(">"):
        continue
    
    i = 0
    while line and line[i] in string.digits:
        i += 1
    
    # Map the old line number to the new one.
    number = int(line[:i])
    numbers[number] = n
    
    line = line[i:].rstrip()
    
    if line == ":---" or line.startswith("REM") or line == ":":
        continue
    
    for s in "\\", ": REM", ":REM":
        at = line.find(s)
        if at != -1:
            line = line[:at]
    
    lines.append(line)
    
    for r in int_r, str_r:
        for match in r.finditer(line):
            variables.add(match.group())
    
    for match in proc_r.finditer(line):
        procedures.add(match.group())
    
    n += 10

# Simplify variable names.
used = set()
replacements = {}

for name in variables:
    new_name = ""
    for c in name[:-1]:
        new_name += c
        if new_name not in used:
            used.add(new_name)
            replacements[name] = new_name + name[-1]
            break
    else:
        replacements[name] = name
    
    #print name, "->", replacements[name]

# Simplify procedure names.
used = set()

for name in procedures:
    new_name = ""
    for c in name[4:]:
        new_name += c
        if new_name not in used:
            used.add(new_name)
            replacements[name] = "PROC" + new_name
            break
    else:
        replacements[name] = name
    
    #print name, "->", replacements[name]


n = 10
for line in lines:

    # Replace old line numbers used with GOTO and RESTORE statements.
    
    for token in "GOTO", "RESTORE":
    
        at = 0
        while at < len(line):
        
            at = line.find(token, at)
            
            if at == -1:
                break
            
            at += len(token)
            i = at
            while i < len(line):
            
                if line[i] == " ":
                    at = i = i + 1
                elif line[i] in string.digits:
                    i += 1
                else:
                    break
            
            old_n = int(line[at:i])
            rest = line[i:]
            line = line[:at] + str(numbers[old_n])
            at = len(line)
            line += rest
    
    # Replace variable and procedure names with shorter ones.
    
    for r in int_r, str_r, proc_r:
    
        l = ""
        i = 0
        for match in r.finditer(line):
            l += line[i:match.start()] + replacements[match.group()]
            i = match.end()
        
        if i < len(line):
            l += line[i:]
        
        line = l
    
    f.write(str(n) + " " + line + "\r")
    n += 10

length = f.tell()
f.close()

f = open("MENU.inf", "w")
f.write("$.Menu 0000 0000 %x" % length)
f.close()
