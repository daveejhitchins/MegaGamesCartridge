#!/usr/bin/env python

import os, re, stat, string

text = open("Menu50M").read()
f = open("MENU", "w")

lines = []
non_appendable = set()
variables = set()
procedure_defs = {}
procedure_calls = set()
int_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)%")
str_r = re.compile(r"(([A-Z][a-z]+[0-9]?)+)\$")
proc_r = re.compile(r"(DEF)?(PROC)(([A-Za-z]+)+)")
hspace_r = re.compile(r'("[^"]+")')
assign_r = re.compile(r'[A-Za-z0-9]+[%$]=(([A-Za-z0-9]+[%$])|([0-9]+)|("[^"]+"))(\+[0-9]+)?')

space_tokens = ["IF", "THEN", "ELSE", "<", ">", "AND", "OR", r"\+", r"\-",
                "\*", ":", "DEF", "PROC", "FN", "DIV", "MOD", "TAB"]
space_r = []
for token in space_tokens:
    space_r.append((re.compile(r"( *" + token + " *)"), token))

par_tokens = ["SPC", r"CHR\$"]
par_r = []
for token in par_tokens:
    par_r.append((re.compile(token + r'\(([0-9A-Za-z]+)\)'), token))

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
    
    for r, token in par_r:
        token = token.replace("\\", "")
        i = 0
        while i < len(line):
            match = r.search(line, i)
            if not match: break
            repl = token + match.groups()[0]
            line = line[:match.start()] + repl + line[match.end():]
            i = match.start() + len(repl)
    
    return line


# Read the lines in the program, mapping line numbers to line contents and
# recording which line numbers are referred to by GOTO and RESTORE statements.
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


# Process the program, removing unnecessary characters, concatenating lines,
# and mapping old line numbers to new ones.
n = 10
can_extend = False
proc_name = None
in_proc = None

for number, line in new_lines:
    
    i = 0
    while line and line[i] in string.digits:
        i += 1
    
    if line == ":---" or line.startswith("REM") or line == ":":
        continue
    
    for r in int_r, str_r:
        for match in r.finditer(line):
            variables.add(match.group())
    
    old_line = line
    line = strip_line(line)
    
    if line.startswith("END") and lines:
        match = proc_r.search(lines[-1][1])
        if match and match.group(1) == "DEF" and ":" not in lines[-1][1]:
            print "PROC", match.group(3), "is empty."
    
    for match in proc_r.finditer(line):
        proc_name = match.group(3)
        if match.group(1) == "DEF":
            procedure_defs[proc_name] = [number]
            in_proc = proc_name
        else:
            procedure_calls.add(proc_name)
    
    if line.startswith("END") and in_proc in procedure_defs:
        procedure_defs[in_proc].append(number)
        in_proc = None
    
    for token in initial:
        if token in line:
            appendable = False
            break
    else:
        appendable = True
    
    match = assign_r.match(line)
    assignment = match and match.span() == (0, len(line))
    assembly = "\\" in old_line and not line.startswith(".")
    
    if assignment or assembly:
        if can_extend:
            combined = lines[-1][1] + ":" + line
            if len(combined) < 240:
                lines[-1] = (lines[-1][0], combined)
                continue
        
        can_extend = True
    else:
        can_extend = False
    
    #if lines and appendable and number not in non_appendable:
    #    for token in control:
    #        if token in lines[-1][1]: break
    #    else:
    #        combined = lines[-1][1] + ":" + line
    #        if len(combined) < 256:
    #            lines[-1] = (lines[-1][0], combined)
    #            continue
    
    line = line.replace("THEN", "")
    
    lines.append((number, line))


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

# Remove used procedures from the definitions dictionary, leaving only unused
# ones. Additionally, removed incomplete definitions.
for name, span in procedure_defs.items():
    if name in procedure_calls or len(span) == 1:
        del procedure_defs[name]

# Simplify procedure names.
used = set()

for name in procedure_calls:
    new_name = ""
    for c in name:
        new_name += c
        if new_name not in used:
            used.add(new_name)
            replacements[name] = new_name
            break
    else:
        replacements[name] = name
    
    #print name, "->", replacements[name]


# Collect the spans of unused procedures.
removed_spans = map(lambda (k, v): (v, k), procedure_defs.items())
removed_spans.sort()

numbers = {}
new_lines = []
n = 10

for number, line in lines:

    # Map the old line number to the new one.
    numbers[number] = n
    
    # Removed unused procedures.
    if removed_spans:
    
        # Examine the first span.
        (begin, end), proc_name = removed_spans[0]
        if begin <= number <= end:
            if number == end:
                print "Removed", proc_name, removed_spans.pop(0)[0]
            continue
    
    new_lines.append((n, line))
    n += 10


for number, line in new_lines:

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
        
            if r == proc_r:
                if match.group(1):
                    prefix = "DEFPROC"
                else:
                    prefix = "PROC"
                l += line[i:match.start()] + prefix + replacements[match.group(3)]
            else:
                l += line[i:match.start()] + replacements[match.group()]
            i = match.end()
        
        if i < len(line):
            l += line[i:]
        
        line = l
    
    f.write(str(number) + line + "\r")

length = f.tell()
f.close()

f = open("MENU.inf", "w")
f.write("$.Menu 0000 0000 %x" % length)
f.close()
