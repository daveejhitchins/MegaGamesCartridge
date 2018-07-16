#!/usr/bin/env python

import os, re, stat, string

text = open("Menu50M").read()
f = open("MENU", "w")

lines = []
numbers = {}
non_appendable = set()
variables = set()
procedures = set()
int_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)%")
str_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)\$")
proc_r = re.compile(r"(PROC([A-Z][a-z]+)+)")

space_tokens = ["IF", "THEN", "<", ">", "AND", "OR", r"\+", r"\-", "\*", ":",
                "DEF", "PROC", "FN", "DIV", "MOD"]
space_r = []
for token in space_tokens:
    space_r.append((re.compile(r"( *" + token + " *)"), token))

control = ["FOR", "NEXT", "IF", "ELSE", "REPEAT", "UNTIL", "ENDPROC", "END",
           "*FX", "DIM", "DEF"]
initial = ["DEF", "DIM"]

def read_number(line, at):

    i = at
    while i < len(line):
    
        if line[i] == " ":
            at = i = i + 1
        elif line[i] in string.digits:
            i += 1
        else:
            break
    
    return int(line[at:i]), i

def strip_line(line):

    for s in "\\", ": REM", ":REM":
        at = line.find(s)
        if at != -1:
            line = line[:at].rstrip()
    
    for r, token in space_r:
        repl = token.lstrip("\\")
        i = 0
        while i < len(line):
            match = r.search(line, i)
            if not match: break
            line = line[:match.start()] + repl + line[match.end():]
            i = match.start() + len(repl)
    
    return line


old_lines = text.split("\r")
new_lines = []

for line in old_lines:

    line = line.lstrip()
    if not line or line.startswith(">"):
        continue
    
    i = 0
    while line and line[i] in string.digits:
        i += 1
    
    number = int(line[:i])
    line = line[i:].rstrip()
    
    for token in "GOTO", "RESTORE":
    
        at = 0
        while at < len(line):
        
            at = line.find(token, at)
            
            if at == -1:
                break
            
            at += len(token)
            old_n, i = read_number(line, at)
            non_appendable.add(old_n)
    
    new_lines.append((number, line))

n = 10

for number, line in new_lines:
    
    i = 0
    while line and line[i] in string.digits:
        i += 1
    
    # Map the old line number to the new one.
    numbers[number] = n
    
    if line == ":---" or line.startswith("REM") or line == ":":
        continue
    
    for r in int_r, str_r:
        for match in r.finditer(line):
            variables.add(match.group())
    
    for match in proc_r.finditer(line):
        procedures.add(match.group())
    
    line = strip_line(line)
    for token in initial:
        if token in line:
            appendable = False
            break
    else:
        appendable = True
    
    #if lines and appendable and number not in non_appendable:
    #    for token in control:
    #        if token in lines[-1]: break
    #    else:
    #        combined = lines[-1] + ":" + line
    #        if len(combined) < 256:
    #            lines[-1] = combined
    #            continue
    
    lines.append(line)
    
    n += 10

# Simplify variable names.
used = set()
replacements = {}
variables = map(lambda x: (len(x), x), variables)
variables = map(lambda x: x[1], sorted(variables))

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
            old_n, i = read_number(line, at)
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
    
    f.write(str(n) + line + "\r")
    n += 10

length = f.tell()
f.close()

f = open("MENU.inf", "w")
f.write("$.Menu 0000 0000 %x" % length)
f.close()
